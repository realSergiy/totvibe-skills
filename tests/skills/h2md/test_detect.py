from __future__ import annotations


def test_detects_fused_text(h2md, workspace):
    fused = "a" * 60
    md = f"# Title\n\nSome text {fused} more text.\n"
    (workspace / "article.md").write_text(md)
    h2md._detect(workspace)
    notes = (workspace / "notes.md").read_text()
    assert "fused text" in notes.lower()


def test_detects_html_leakage(h2md, workspace):
    md = '# Title\n\nSome text <svg viewBox="0 0 10 10"> leftover.\n'
    (workspace / "article.md").write_text(md)
    h2md._detect(workspace)
    notes = (workspace / "notes.md").read_text()
    assert "HTML leakage" in notes


def test_detects_suspicious_tab_labels(h2md, workspace):
    md = "# Title\n\ncurl\n```bash\ncurl https://example.com\n```\n"
    (workspace / "article.md").write_text(md)
    h2md._detect(workspace)
    notes = (workspace / "notes.md").read_text()
    assert "tab label" in notes.lower()


def test_clean_file_no_notes(h2md, workspace):
    md = "# Title\n\nClean paragraph with normal text.\n"
    (workspace / "article.md").write_text(md)
    h2md._detect(workspace)
    notes = (workspace / "notes.md").read_text()
    assert notes.strip() == ""


def test_uses_substring_anchors(h2md, workspace):
    fused = "x" * 60
    md = f"# Title\n\nBefore the problem {fused} after it.\n"
    (workspace / "article.md").write_text(md)
    h2md._detect(workspace)
    notes = (workspace / "notes.md").read_text()
    assert "**Find:**" in notes
    assert "line" not in notes.lower().split("find")[0]
