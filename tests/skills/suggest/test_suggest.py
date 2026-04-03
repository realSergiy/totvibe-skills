"""Tests for the suggest skill."""

from __future__ import annotations

from pathlib import Path


def test_saves_suggestion_file(invoke, suggest, tmp_path):
    suggest.SUGGEST_DIR = tmp_path
    result = invoke("peek", "## Bug\n\nSomething broke")
    assert result.exit_code == 0
    files = list((tmp_path / "peek").glob("suggestion_*.md"))
    assert len(files) == 1
    assert files[0].read_text() == "## Bug\n\nSomething broke\n"
    assert "saved:" in result.output


def test_output_contains_path(invoke, suggest, tmp_path):
    suggest.SUGGEST_DIR = tmp_path
    result = invoke("peek", "test text")
    assert result.exit_code == 0
    path = result.output.strip().removeprefix("saved: ")
    assert Path(path).exists()


def test_creates_skill_subdirectory(invoke, suggest, tmp_path):
    suggest.SUGGEST_DIR = tmp_path
    result = invoke("newskill", "some suggestion")
    assert result.exit_code == 0
    assert (tmp_path / "newskill").is_dir()


def test_multiple_suggestions_different_timestamps(invoke, suggest, tmp_path):
    suggest.SUGGEST_DIR = tmp_path
    invoke("peek", "first")
    invoke("peek", "second")
    files = sorted((tmp_path / "peek").glob("suggestion_*.md"))
    assert len(files) >= 1
    contents = [f.read_text() for f in files]
    assert "second\n" in contents


def test_missing_args_fails(invoke):
    result = invoke()
    assert result.exit_code != 0


def test_missing_text_fails(invoke):
    result = invoke("peek")
    assert result.exit_code != 0


def test_markdown_content_preserved(invoke, suggest, tmp_path):
    suggest.SUGGEST_DIR = tmp_path
    md = "## Feature request\n\n- bullet one\n- bullet two\n\n```python\nprint('hello')\n```"
    result = invoke("peek", md)
    assert result.exit_code == 0
    files = list((tmp_path / "peek").glob("suggestion_*.md"))
    assert files[0].read_text() == md + "\n"
