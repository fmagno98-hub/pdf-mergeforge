from pathlib import Path

from pdf_merger_desktop import word_worker


def test_worker_forwards_layout_and_ghostscript(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "result.docx"
    ghostscript = r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe"
    observed = {}

    def convert(paths, target, progress, cancelled, *, preserve_layout, ghostscript_path):
        observed.update(
            paths=paths,
            target=target,
            preserve_layout=preserve_layout,
            ghostscript_path=ghostscript_path,
        )
        return target, 1, 1

    monkeypatch.setattr(word_worker, "convert_pdfs_to_docx", convert)
    worker = word_worker.WordWorker([source], output, True, ghostscript)
    worker.run()

    assert observed == {
        "paths": [source],
        "target": output,
        "preserve_layout": True,
        "ghostscript_path": ghostscript,
    }
