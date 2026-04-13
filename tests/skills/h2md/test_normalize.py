from __future__ import annotations

import json


def _setup_normalize(workspace, raw_md, meta=None):
    (workspace / "article.raw.md").write_text(raw_md)
    if meta is None:
        meta = {"title": "Test Article", "author": "Author", "date": "2026-01-01"}
    (workspace / "meta.json").write_text(json.dumps(meta))


def test_adds_frontmatter(h2md, workspace):
    _setup_normalize(workspace, "# Title\n\nBody text.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert md.startswith("---\n")
    assert 'title: "Test Article"' in md
    assert 'author: "Author"' in md
    assert "---" in md


def test_adds_h1_from_meta(h2md, workspace):
    _setup_normalize(workspace, "No heading here, just text.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert "# Test Article" in md


def test_does_not_duplicate_h1(h2md, workspace):
    _setup_normalize(workspace, "# Existing Title\n\nBody.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert md.count("# ") == 1 or md.count("\n# ") <= 1


def test_promotes_bold_headings(h2md, workspace):
    _setup_normalize(workspace, "# Title\n\n**RFC 6455 Compliant Subprotocol Negotiation**\n\nSome text.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert "#### RFC 6455 Compliant Subprotocol Negotiation" in md
    assert "**RFC 6455" not in md


def test_drops_empty_fences(h2md, workspace):
    _setup_normalize(workspace, "# Title\n\n```\n\n```\n\nKeep this.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert "```" not in md
    assert "Keep this." in md


def test_collapses_blank_lines(h2md, workspace):
    _setup_normalize(workspace, "# Title\n\n\n\n\nBody.\n")
    h2md._normalize(workspace)
    md = (workspace / "article.prelint.md").read_text()
    assert "\n\n\n" not in md
