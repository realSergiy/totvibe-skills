from __future__ import annotations

import json
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from toon_format import decode as _decode
from typer.testing import CliRunner

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def h2md(skill_loader):
    return skill_loader("h2md")


@pytest.fixture
def fixture_dir():
    return FIXTURE_DIR


def _read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text()


@pytest.fixture
def read_fixture():
    return _read_fixture


@pytest.fixture
def decode():
    def _fn(text: str) -> dict[str, Any]:
        result = _decode(text)
        assert isinstance(result, dict)
        return result
    return _fn


def _mock_subprocess_run(*args, **kwargs):
    return subprocess.CompletedProcess(args=args[0] if args else [], returncode=0, stdout="", stderr="")


@pytest.fixture
def serve_html():
    servers: list[HTTPServer] = []

    def _serve(html: str, *, content_type: str = "text/html") -> str:
        body = html.encode()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{port}/article"

    yield _serve

    for s in servers:
        s.shutdown()


@pytest.fixture
def pipeline(h2md, serve_html, decode):
    def _run(html: str, *, selector: str | None = None, url: str | None = None):
        serve_url = serve_html(html)
        cli_args = [url or serve_url, "--no-assets"]
        if selector:
            cli_args.extend(["--selector", selector])
        from unittest.mock import patch
        with patch("subprocess.run", side_effect=_mock_subprocess_run):
            runner = CliRunner()
            result = runner.invoke(h2md.app, cli_args)
        assert result.exit_code == 0, result.output
        d = decode(result.output)
        ws = Path(d["h2md"]["workspace"])
        return SimpleNamespace(
            md=(ws / "article.md").read_text(),
            meta=json.loads((ws / "meta.json").read_text()),
            notes=(ws / "notes.md").read_text(),
            toon=d,
            workspace=ws,
        )
    return _run
