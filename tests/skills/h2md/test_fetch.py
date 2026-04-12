from __future__ import annotations

import json


def test_manifest_save_load_roundtrip(h2md, tmp_path):
    m = h2md.Manifest(url="https://example.com/post")
    m.mark_done("fetch", 1.5, raw_html="abc123")
    path = tmp_path / "h2md.json"
    m.save(path)
    loaded = h2md.Manifest.load(path)
    assert loaded.url == "https://example.com/post"
    assert loaded.stage_done("fetch")
    assert loaded.timings["fetch"] == 1.5
    assert loaded.checksums["raw_html"] == "abc123"


def test_manifest_stage_done(h2md):
    m = h2md.Manifest(url="https://x.com")
    assert not m.stage_done("fetch")
    m.mark_done("fetch", 0.1)
    assert m.stage_done("fetch")


def test_url_to_slug(h2md):
    assert h2md._url_to_slug("https://bun.com/blog/bun-v1.3") == "bun_com_blog_bun-v1_3"
    assert h2md._url_to_slug("https://deno.com/blog/v2.7") == "deno_com_blog_v2_7"
    assert h2md._url_to_slug("https://www.example.com/") == "example_com"


def test_fetch_creates_files(h2md, workspace, mock_fetch):
    html = "<html><body>Hello</body></html>"
    manifest = h2md.Manifest(url="https://example.com/article")
    with mock_fetch(html):
        h2md._fetch(workspace, manifest, "https://example.com/article", force=False)
    assert (workspace / "source.url").read_text().strip() == "https://example.com/article"
    assert (workspace / "raw.html").read_text() == html
    headers = json.loads((workspace / "raw.headers.json").read_text())
    assert headers["status_code"] == 200
    assert manifest.stage_done("fetch")
    assert "raw_html" in manifest.checksums


def test_fetch_skips_when_done(h2md, workspace, mock_fetch):
    manifest = h2md.Manifest(url="https://example.com")
    manifest.mark_done("fetch", 0.1)
    with mock_fetch("<html></html>") as ctx:
        h2md._fetch(workspace, manifest, "https://example.com", force=False)
        ctx.__enter__().get.assert_not_called()


def test_fetch_force_reruns(h2md, workspace, mock_fetch):
    html = "<html><body>New</body></html>"
    manifest = h2md.Manifest(url="https://example.com")
    manifest.mark_done("fetch", 0.1)
    with mock_fetch(html):
        h2md._fetch(workspace, manifest, "https://example.com", force=True)
    assert (workspace / "raw.html").read_text() == html
