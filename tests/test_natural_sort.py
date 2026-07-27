from pdf_merger_desktop.utilities.natural_sort import natural_key


def test_natural_ascending() -> None:
    assert sorted(["file10.pdf", "file2.pdf", "file9.pdf"], key=natural_key) == [
        "file2.pdf",
        "file9.pdf",
        "file10.pdf",
    ]


def test_natural_descending_and_case_insensitive() -> None:
    names = ["B2.pdf", "a10.pdf", "A2.pdf"]
    assert sorted(names, key=natural_key, reverse=True) == ["B2.pdf", "a10.pdf", "A2.pdf"]
