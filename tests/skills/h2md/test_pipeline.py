from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from typer.testing import CliRunner


def _mock_subprocess_run(*args, **kwargs):
    return subprocess.CompletedProcess(args=args[0] if args else [], returncode=0, stdout="", stderr="")


def _run_pipeline(h2md, mock_fetch, html, extra_args=None):
    cli_args = ["https://example.com/x", "--no-assets"]
    if extra_args:
        cli_args.extend(extra_args)
    with mock_fetch(html), patch("subprocess.run", side_effect=_mock_subprocess_run):
        runner = CliRunner()
        return runner.invoke(h2md.app, cli_args)


def test_full_pipeline_simple_article(h2md, read_fixture, mock_fetch, decode):
    html = read_fixture("simple_article.html")
    result = _run_pipeline(h2md, mock_fetch, html)
    assert result.exit_code == 0, result.output

    decoded = decode(result.output)
    assert "h2md" in decoded
    assert decoded["h2md"]["words"] > 0

    workspace = decoded["h2md"]["workspace"]
    from pathlib import Path
    ws = Path(workspace)
    for name in ["source.url", "raw.html", "raw.headers.json", "article.html",
                  "meta.json", "article.raw.md", "article.prelint.md", "article.md",
                  "notes.md"]:
        assert (ws / name).exists(), f"Missing: {name}"

    meta = json.loads((ws / "meta.json").read_text())
    assert meta["title"] == "Getting Started with FastAPI"
    assert meta["author"] == "Jane Smith"

    md = (ws / "article.md").read_text()
    assert "FastAPI" in md
    assert "pip install fastapi" in md


def test_version_flag(h2md):
    runner = CliRunner()
    result = runner.invoke(h2md.app, ["--version"])
    assert result.exit_code == 0
    assert "h2md" in result.output
    assert h2md.__version__ in result.output


def test_js_flag_errors(h2md):
    runner = CliRunner()
    result = runner.invoke(h2md.app, ["https://example.com", "--js"])
    assert result.exit_code != 0
    assert "playwright" in result.output.lower()
