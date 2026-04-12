from __future__ import annotations

import json


def test_jsonld_takes_priority(h2md, read_fixture, workspace):
    html = read_fixture("metadata_rich.html")
    (workspace / "raw.html").write_text(html)
    (workspace / "article.html").write_text("<p>Test article content for word count estimation.</p>")
    manifest = h2md.Manifest(url="https://example.com")
    h2md._metadata(workspace, manifest, force=True)
    meta = json.loads((workspace / "meta.json").read_text())
    assert meta["title"] == "JSON-LD Headline"
    assert meta["author"] == "JSON-LD Author"
    assert meta["date"] == "2026-01-20T08:00:00Z"


def test_og_fills_gaps(h2md, read_fixture, workspace):
    html = read_fixture("metadata_rich.html")
    (workspace / "raw.html").write_text(html)
    (workspace / "article.html").write_text("<p>Content</p>")
    manifest = h2md.Manifest(url="https://example.com")
    h2md._metadata(workspace, manifest, force=True)
    meta = json.loads((workspace / "meta.json").read_text())
    assert meta["og_image"] == "https://example.com/og-image.jpg"
    assert meta["site_name"] == "Example Site"


def test_canonical_url_from_jsonld(h2md, read_fixture, workspace):
    html = read_fixture("simple_article.html")
    (workspace / "raw.html").write_text(html)
    (workspace / "article.html").write_text("<p>Content</p>")
    manifest = h2md.Manifest(url="https://example.com")
    h2md._metadata(workspace, manifest, force=True)
    meta = json.loads((workspace / "meta.json").read_text())
    assert "canonical_url" in meta


def test_word_count_and_reading_time(h2md, workspace):
    words = " ".join(["word"] * 500)
    (workspace / "raw.html").write_text(f"<html><head><title>Test</title></head><body><p>{words}</p></body></html>")
    (workspace / "article.html").write_text(f"<p>{words}</p>")
    manifest = h2md.Manifest(url="https://example.com")
    h2md._metadata(workspace, manifest, force=True)
    meta = json.loads((workspace / "meta.json").read_text())
    assert meta["word_count"] == 500
    assert meta["reading_time_minutes"] == 2


def test_lang_from_html_tag(h2md, read_fixture, workspace):
    html = read_fixture("metadata_rich.html")
    (workspace / "raw.html").write_text(html)
    (workspace / "article.html").write_text("<p>Content</p>")
    manifest = h2md.Manifest(url="https://example.com")
    h2md._metadata(workspace, manifest, force=True)
    meta = json.loads((workspace / "meta.json").read_text())
    assert meta["lang"] == "fr"
