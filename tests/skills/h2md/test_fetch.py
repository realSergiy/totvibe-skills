from __future__ import annotations

import json


def test_fetch_creates_files(h2md, workspace, mock_fetch):
    html = "<html><body>Hello</body></html>"
    with mock_fetch(html):
        h2md._fetch(workspace, "https://example.com/article")
    assert (workspace / "source.url").read_text().strip() == "https://example.com/article"
    assert (workspace / "raw.html").read_text() == html
    headers = json.loads((workspace / "raw.headers.json").read_text())
    assert headers["status_code"] == 200
