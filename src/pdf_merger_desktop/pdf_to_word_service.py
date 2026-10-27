"""Local PDF-to-DOCX conversion using pypdf and standard-library OOXML."""

from contextlib import suppress
import math
import os
import re
import struct
import uuid
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader

from .pdf_service import PdfValidationError, validate_sources


class PdfToWordCancelled(RuntimeError):
    """Raised when the user cancels a conversion."""


class PdfToWordError(RuntimeError):
    """Raised when a conversion cannot be completed."""



_BULLET_LINE = re.compile(r"^([ \t]*)([\uf0b7\u2022\u2023\u25e6\u25aa\u25cf\u25cb\u2219\u2043\u00b7])(?:[ \t]+)(.*)$")
_NUMBER_LINE = re.compile(r"^([ \t]*)(\d{1,3})[.)](?:[ \t]+)(.*)$")


def _truetype_names(data: bytes) -> tuple[str | None, str | None]:
    """Read family/style names from an embedded TrueType font without extra packages."""
    if len(data) < 12 or data[:4] not in {b"\x00\x01\x00\x00", b"true"}:
        return None, None
    table_count = struct.unpack_from(">H", data, 4)[0]
    for index in range(table_count):
        record = 12 + index * 16
        if record + 16 > len(data) or data[record:record + 4] != b"name":
            continue
        offset, length = struct.unpack_from(">II", data, record + 8)
        table = data[offset:offset + length]
        if len(table) < 6:
            return None, None
        count, strings_offset = struct.unpack_from(">HH", table, 2)
        found: dict[int, tuple[int, str]] = {}
        for entry in range(count):
            at = 6 + entry * 12
            if at + 12 > len(table):
                break
            platform, _encoding, language, name_id, size, string_offset = struct.unpack_from(">HHHHHH", table, at)
            if name_id not in {1, 2, 16, 17}:
                continue
            value = table[strings_offset + string_offset:strings_offset + string_offset + size]
            try:
                decoded = value.decode("utf-16-be" if platform in {0, 3} else "mac_roman").strip("\x00 ")
            except (UnicodeDecodeError, LookupError):
                continue
            if not decoded:
                continue
            score = (0 if language in {0, 0x0409} else 1) + (0 if platform in {0, 3} else 2)
            if name_id not in found or score < found[name_id][0]:
                found[name_id] = (score, decoded)
        family = found.get(16, found.get(1, (0, None)))[1]
        style = found.get(17, found.get(2, (0, None)))[1]
        return family, style
    return None, None


def _pdf_font_styles(page) -> dict[str, tuple[str | None, bool, bool]]:
    """Map PDF font resources to the real family and style in embedded fonts."""
    styles: dict[str, tuple[str | None, bool, bool]] = {}
    try:
        resources = page.get("/Resources").get_object()
        fonts = resources.get("/Font").get_object()
    except (AttributeError, KeyError, TypeError):
        return styles
    for resource_name, reference in fonts.items():
        try:
            font = reference.get_object()
            base_name = str(font.get("/BaseFont", "")).lstrip("/")
            descriptor = font.get("/FontDescriptor")
            descendants = font.get("/DescendantFonts")
            if descendants:
                descriptor = descendants[0].get_object().get("/FontDescriptor")
            family = style = None
            if descriptor:
                descriptor = descriptor.get_object()
                font_file = descriptor.get("/FontFile2")
                if font_file:
                    family, style = _truetype_names(font_file.get_object().get_data())
            if not family:
                family = re.sub(r"^[A-Z]{6}\+", "", base_name).split(",")[0]
                family = re.sub(r"-(Bold|Italic|Oblique|Regular|MT)$", "", family, flags=re.I)
            style_text = (style or base_name).casefold()
            metadata = (
                family,
                any(word in style_text for word in ("bold", "demi", "black", "heavy")),
                any(word in style_text for word in ("italic", "oblique", "corsivo")),
            )
            styles[str(resource_name)] = metadata
            styles[base_name] = metadata
            styles["/" + base_name] = metadata
        except (AttributeError, KeyError, TypeError, ValueError, struct.error):
            continue
    return styles


def _page_text_style(page) -> tuple[str | None, bool, bool, int | None]:
    """Choose the dominant embedded font and point size used on a PDF page."""
    resources = _pdf_font_styles(page)
    counts: Counter[str] = Counter()
    sizes: Counter[tuple[str, int]] = Counter()

    def collect(text, matrix, _text_matrix, font, font_size):
        if not text or not font:
            return
        resource = str(font.get("/BaseFont", ""))
        count = sum(not character.isspace() for character in text)
        if not count:
            return
        scale = math.hypot(float(matrix[0]), float(matrix[1])) if matrix else 1.0
        points = max(1, min(1638, round(float(font_size) * scale * 2)))
        counts[resource] += count
        sizes[(resource, points)] += count

    with suppress(KeyError, TypeError, ValueError):
        page.extract_text(visitor_text=collect)
    if not counts:
        return None, False, False, None
    dominant = counts.most_common(1)[0][0]
    family, bold, italic = resources.get(dominant, (None, False, False))
    size = next((size for (resource, size), _ in sizes.most_common() if resource == dominant), None)
    return family, bold, italic, size


def _image_type(name: str) -> tuple[str, str]:
    extension = Path(name).suffix.casefold()
    return {
        ".jpg": ("image/jpeg", "jpg"),
        ".jpeg": ("image/jpeg", "jpg"),
        ".gif": ("image/gif", "gif"),
        ".bmp": ("image/bmp", "bmp"),
        ".tif": ("image/tiff", "tif"),
        ".tiff": ("image/tiff", "tif"),
        ".jp2": ("image/jp2", "jp2"),
    }.get(extension, ("image/png", "png"))


def _image_dimensions(data: bytes) -> tuple[int, int]:
    """Read common raster dimensions without adding an imaging dependency."""
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        index = 2
        sof = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            length = int.from_bytes(data[index:index + 2], "big")
            if marker in sof and index + 7 <= len(data):
                return int.from_bytes(data[index + 5:index + 7], "big"), int.from_bytes(data[index + 3:index + 5], "big")
            index += max(length, 2)
    return 1, 1


def _image_xml(rel_id: str, name: str, number: int, width: int, height: int) -> str:
    """Create an editable inline image, fit to the page without distortion."""
    max_width, max_height = 5669280, 7772400
    source_cx = max(1, width) * 9525  # pixels to EMU at 96 DPI
    source_cy = max(1, height) * 9525
    scale = min(1.0, max_width / source_cx, max_height / source_cy)
    cx = max(1, int(source_cx * scale))
    cy = max(1, int(source_cy * scale))
    schema = "http" + "://"
    return (
        f'<w:p><w:r><w:drawing><wp:inline><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{number}" name={quoteattr(name)}/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1" xmlns:a="{schema}schemas.openxmlformats.org/drawingml/2006/main"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="{schema}schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="{schema}schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="{schema}schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="0" name={quoteattr(name)}/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed={quoteattr(rel_id)}/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )


def _run_xml(text: str, style: tuple[str | None, bool, bool, int | None]) -> str:
    family, bold, italic, half_points = style
    properties = []
    if family:
        font = quoteattr(family)
        properties.append(f'<w:rFonts w:ascii={font} w:hAnsi={font} w:cs={font}/>')
    if bold:
        properties.append("<w:b/><w:bCs/>")
    if italic:
        properties.append("<w:i/><w:iCs/>")
    if half_points:
        properties.append(f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>')
    rpr = f"<w:rPr>{''.join(properties)}</w:rPr>" if properties else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _text_xml(text: str, style=(None, False, False, None)) -> str:
    runs = []
    for index, line in enumerate(text.split("\n")):
        if index:
            runs.append("<w:r><w:br/></w:r>")
        if line:
            runs.append(_run_xml(line, style))
    return '<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>' + "".join(runs) + "</w:p>"


def _list_paragraph_xml(lines, num_id: int, style) -> str:
    paragraph = (
        '<w:pPr><w:numPr><w:ilvl w:val="0"/>'
        f'<w:numId w:val="{num_id}"/></w:numPr>'
        '<w:spacing w:before="0" w:after="0"/>'
        '<w:ind w:left="720" w:hanging="360"/></w:pPr>'
    )
    runs = []
    for index, line in enumerate(lines):
        if index:
            runs.append("<w:r><w:br/></w:r>")
        if line:
            runs.append(_run_xml(line, style))
    return f"<w:p>{paragraph}{''.join(runs)}</w:p>"


def _page_text_xml(text: str, style, first_num_id: int):
    """Turn glyph bullets and typed numbering into native Word list paragraphs."""
    paragraphs = []
    list_instances = []
    regular_lines = []
    active_kind = None
    active_num_id = None
    active_start = 1
    active_items = []
    content_indent = 0
    next_num_id = first_num_id

    def flush_regular():
        if regular_lines:
            paragraphs.append(_text_xml("\n".join(regular_lines), style))
            regular_lines.clear()

    def flush_list():
        nonlocal active_kind, active_num_id, active_start, active_items
        if active_items:
            paragraphs.extend(_list_paragraph_xml(lines, active_num_id, style) for lines in active_items)
            list_instances.append((active_num_id, 0 if active_kind == "bullet" else 1, active_start))
        active_kind = active_num_id = None
        active_start = 1
        active_items = []

    for line in text.split("\n"):
        bullet = _BULLET_LINE.match(line)
        numbered = _NUMBER_LINE.match(line)
        marker = bullet or numbered
        if marker:
            flush_regular()
            kind = "bullet" if bullet else "number"
            if active_kind != kind:
                flush_list()
                active_kind = kind
                active_num_id = next_num_id
                next_num_id += 1
                active_start = int(numbered.group(2)) if numbered else 1
            item_text = marker.group(3) if numbered else marker.group(3)
            active_items.append([item_text])
            content_indent = marker.start(3)
            continue
        if active_items:
            if not line.strip():
                flush_list()
                regular_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip(" \t"))
            if indent >= max(3, content_indent - 2):
                active_items[-1].append(line.lstrip())
                continue
            flush_list()
        regular_lines.append(line)

    flush_list()
    flush_regular()
    return "".join(paragraphs), next_num_id, list_instances


def _numbering_xml(instances) -> str:
    schema = "http" + "://"
    abstract = []
    for abstract_id, number_format, marker, family in (
        (0, "bullet", "•", "Arial"),
        (1, "decimal", "%1.", "Times New Roman"),
    ):
        abstract.append(
            f'<w:abstractNum w:abstractNumId="{abstract_id}"><w:multiLevelType w:val="singleLevel"/>'
            f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{number_format}"/>'
            f'<w:lvlText w:val={quoteattr(marker)}/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs>'
            '<w:ind w:left="720" w:hanging="360"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii={quoteattr(family)} w:hAnsi={quoteattr(family)}/></w:rPr>'
            '</w:lvl></w:abstractNum>'
        )
    nums = []
    for num_id, abstract_id, start in instances:
        override = f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="{start}"/></w:lvlOverride>' if abstract_id == 1 else ""
        nums.append(
            f'<w:num w:numId="{num_id}"><w:abstractNumId w:val="{abstract_id}"/>{override}</w:num>'
        )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><w:numbering xmlns:w="{schema}schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + "".join(abstract + nums)
        + "</w:numbering>"
    )


def convert_pdfs_to_docx(
    paths: Sequence[str | Path],
    output: str | Path,
    progress: Callable[[int, int, str], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
    *,
    preserve_layout: bool = False,
    ghostscript_path: str | None = None,
) -> tuple[Path, int, int]:
    """Extract selectable text and embedded images without Word or Ghostscript.

    Legacy layout arguments are accepted for compatibility with older settings;
    page rasterization is intentionally never used.
    """
    del ghostscript_path
    sources = [Path(path).resolve() for path in paths]
    if not sources:
        raise PdfValidationError("Add at least one PDF file.")
    destination = Path(output).resolve()
    if destination.suffix.casefold() != ".docx":
        destination = destination.with_suffix(".docx")
    validate_sources(sources, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.stem}-{uuid.uuid4().hex}.tmp.docx"
    body: list[str] = []
    media: list[tuple[str, bytes, str, str]] = []
    page_count = image_count = 0
    next_num_id = 1
    list_instances = []
    total = sum(len(PdfReader(source, strict=False).pages) for source in sources)
    schema = "http" + "://"
    try:
        for source in sources:
            reader = PdfReader(source, strict=False)
            for page in reader.pages:
                if cancelled and cancelled():
                    raise PdfToWordCancelled("Conversion cancelled")
                page_count += 1
                if progress:
                    progress(page_count, total, source.name)
                try:
                    text = page.extract_text(extraction_mode="layout" if preserve_layout else "plain") or ""
                except (KeyError, TypeError, ValueError):
                    text = ""
                if not text.strip():
                    text = "[No text layer detected on this page]"
                page_style = _page_text_style(page)
                page_xml, next_num_id, page_lists = _page_text_xml(
                    text.rstrip(), page_style, next_num_id
                )
                body.append(page_xml)
                list_instances.extend(page_lists)
                for image in page.images:
                    content_type, extension = _image_type(image.name)
                    image_count += 1
                    filename = f"image{image_count}.{extension}"
                    rel_id = f"rId{image_count + 1}"
                    media.append((filename, image.data, content_type, rel_id))
                    width, height = _image_dimensions(image.data)
                    body.append(_image_xml(rel_id, image.name, image_count, width, height))
                if page_count < total:
                    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

        relationships = "".join(
            f'<Relationship Id="{rel_id}" Type="{schema}schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{filename}"/>'
            for filename, _, _, rel_id in media
        )
        unique_types = dict.fromkeys((filename.rsplit(".", 1)[1], mime) for filename, _, mime, _ in media)
        content_types = (
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(f'<Default Extension="{ext}" ContentType="{mime}"/>' for ext, mime in unique_types)
            + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        )
        numbering_path = ""
        numbering_type = ""
        if list_instances:
            numbering_rel_id = f"rId{image_count + 2}"
            relationships += (
                f'<Relationship Id="{numbering_rel_id}" Type="{schema}schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
            )
            numbering_path = _numbering_xml(list_instances)
            numbering_type = (
                '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
            )
        content_types += numbering_type
        document = (
            f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{schema}schemas.openxmlformats.org/wordprocessingml/2006/main" '
            f'xmlns:r="{schema}schemas.openxmlformats.org/officeDocument/2006/relationships" '
            f'xmlns:wp="{schema}schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><w:body>'
            + "".join(body)
            + '<w:sectPr><w:pgSz w:w="11905" w:h="16837"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>'
        )
        types_xml = f'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="{schema}schemas.openxmlformats.org/package/2006/content-types">{content_types}</Types>'
        root_rels = f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{schema}schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{schema}schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
        document_rels = f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{schema}schemas.openxmlformats.org/package/2006/relationships">{relationships}</Relationships>'
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", types_xml)
            archive.writestr("_rels/.rels", root_rels)
            archive.writestr("word/document.xml", document)
            archive.writestr("word/_rels/document.xml.rels", document_rels)
            if numbering_path:
                archive.writestr("word/numbering.xml", numbering_path)
            for filename, data, _, _ in media:
                archive.writestr(f"word/media/{filename}", data)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise PdfToWordError("The Word output could not be verified.")
        os.replace(temporary, destination)
        return destination, page_count, image_count
    finally:
        temporary.unlink(missing_ok=True)
