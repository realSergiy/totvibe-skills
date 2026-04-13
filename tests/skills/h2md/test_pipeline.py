from __future__ import annotations

from typer.testing import CliRunner


def test_full_pipeline_produces_expected_outputs(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    assert r.toon["h2md"]["words"] > 0
    assert "article" in r.toon["h2md"]["article"]
    assert r.md
    assert r.meta
    assert isinstance(r.notes, str)


def test_pipeline_workspace_has_final_files(pipeline, read_fixture):
    r = pipeline(read_fixture("simple_article.html"))
    for name in ["article.md", "meta.json", "notes.md", "article.html"]:
        assert (r.workspace / name).exists(), f"Missing: {name}"


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
