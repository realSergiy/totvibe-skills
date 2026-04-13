from __future__ import annotations

import subprocess
from unittest.mock import patch

from typer.testing import CliRunner


def _mock_subprocess_run(*args, **kwargs):
    return subprocess.CompletedProcess(args=args[0] if args else [], returncode=0, stdout="", stderr="")


def test_full_pipeline_produces_expected_outputs(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    h = r.toon["h2md"]
    assert h["words"] > 0
    assert h["article"] == "article.md"
    assert "issues" in h
    assert "lint_remaining" in h
    toc = r.toon["toc"]
    assert "total_sections" in toc
    assert "total_code_blocks" in toc
    assert "toc.toon" in r.toon["next"]
    assert r.md
    assert r.meta
    assert isinstance(r.notes, str)


def test_pipeline_workspace_has_final_files(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    for name in ["article.md", "meta.json", "notes.md", "article.html", "toc.toon"]:
        assert (r.workspace / name).exists(), f"Missing: {name}"


def test_toc_manifest_structure(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    sections = r.toc["sections"]
    assert len(sections) > 0
    assert set(sections[0].keys()) == {"level", "title", "line", "words", "code_blocks", "issues"}
    summary = r.toc["summary"]
    assert summary["total_sections"] == len(sections)
    assert "total_code_blocks" in summary
    assert "code_languages" in summary
    assert "total_issues" in summary
    assert "sections_with_issues" in summary


def test_toc_manifest_counts_code_blocks(pipeline):
    html = """<!DOCTYPE html><html><body><article>
    <h1>Guide</h1>
    <p>This guide shows how to use the API with several code examples and explanations for developers.</p>
    <h2>Setup</h2>
    <p>Install the package first before proceeding with configuration for the project.</p>
    <pre><code class="language-bash">npm install example</code></pre>
    <h2>Usage</h2>
    <p>First import the package into your application code for the main feature:</p>
    <pre><code class="language-javascript">import { foo } from 'example'</code></pre>
    <p>Then call the function to get the result you need from the library:</p>
    <pre><code class="language-javascript">const result = foo()</code></pre>
    </article></body></html>"""
    r = pipeline(html)
    sections = {s["title"]: s for s in r.toc["sections"]}
    assert sections["Guide"]["code_blocks"] == 0
    assert sections["Setup"]["code_blocks"] == 1
    assert sections["Usage"]["code_blocks"] == 2
    assert r.toc["summary"]["total_code_blocks"] == 3
    assert r.toc["summary"]["code_languages"] == {"bash": 1, "javascript": 2}


def test_version_flag(h2md):
    runner = CliRunner()
    result = runner.invoke(h2md.app, ["--version"])
    assert result.exit_code == 0
    assert "h2md" in result.output


def test_js_flag_errors(h2md):
    runner = CliRunner()
    result = runner.invoke(h2md.app, ["https://example.com", "--js"])
    assert result.exit_code != 0
    assert "playwright" in result.output.lower()


def test_copy_to_flag(h2md, serve_html, decode, read_fixture, tmp_path):
    url = serve_html(read_fixture("simple_article.html"))
    dest = tmp_path / "output.md"
    with patch("subprocess.run", side_effect=_mock_subprocess_run):
        runner = CliRunner()
        result = runner.invoke(h2md.app, [url, "--no-assets", "--copy-to", str(dest)])
    assert result.exit_code == 0, result.output
    assert dest.exists()
    assert dest.read_text().strip()
