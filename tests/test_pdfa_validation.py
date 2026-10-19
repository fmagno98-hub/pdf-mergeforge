from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject

from pdf_merger_desktop.services.pdfa_validation_service import validate_pdfa_baseline


def make_claimed_pdfa(path: Path, *, part: str = "1", conformance: str = "B") -> Path:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    metadata = DecodedStreamObject()
    metadata.set_data(
        f"<x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF xmlns:rdf='rdf' "
        f"xmlns:pdfaid='http://www.aiim.org/pdfa/ns/id/'><rdf:Description "
        f"pdfaid:part='{part}' pdfaid:conformance='{conformance}'/></rdf:RDF></x:xmpmeta>".encode()
    )
    metadata[NameObject("/Type")] = NameObject("/Metadata")
    metadata[NameObject("/Subtype")] = NameObject("/XML")
    writer.root_object[NameObject("/Metadata")] = writer._add_object(metadata)
    intent = DictionaryObject({NameObject("/Type"): NameObject("/OutputIntent")})
    writer.root_object[NameObject("/OutputIntents")] = ArrayObject([writer._add_object(intent)])
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def test_baseline_accepts_expected_claims(tmp_path: Path) -> None:
    result = validate_pdfa_baseline(make_claimed_pdfa(tmp_path / "ok.pdf"), 1)
    assert result.passed and len(result.checks) == 6


def test_baseline_rejects_wrong_claims_and_page_count(tmp_path: Path) -> None:
    result = validate_pdfa_baseline(
        make_claimed_pdfa(tmp_path / "bad.pdf", part="2", conformance="A"), 2
    )
    assert not result.passed
    assert any("page count" in error for error in result.errors)
    assert any("part 1" in error for error in result.errors)
    assert any("level B" in error for error in result.errors)


def test_baseline_rejects_plain_pdf_without_output_intent(tmp_path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    path = tmp_path / "plain.pdf"
    with path.open("wb") as stream:
        writer.write(stream)
    result = validate_pdfa_baseline(path, 1)
    assert not result.passed and any("OutputIntent" in error for error in result.errors)
