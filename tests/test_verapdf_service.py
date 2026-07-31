import pytest

from pdf_merger_desktop.services.verapdf_service import parse_verapdf_report


@pytest.mark.parametrize("value,expected", [("true", True), ("false", False)])
def test_parse_verapdf_compliance(value: str, expected: bool) -> None:
    xml = f'<report><validationReport isCompliant="{value}"/></report>'
    assert parse_verapdf_report(xml) is expected


@pytest.mark.parametrize("xml", ["not xml", "<report/>", '<validationReport isCompliant="maybe"/>'])
def test_parse_verapdf_rejects_malformed_report(xml: str) -> None:
    with pytest.raises(RuntimeError):
        parse_verapdf_report(xml)
