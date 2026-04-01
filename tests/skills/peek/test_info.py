"""Integration tests for the peek info command."""

from __future__ import annotations

import pytest


def test_exits_successfully(invoke):
    result = invoke("info")
    assert result.exit_code == 0


def test_reports_row_count(invoke, decode):
    result = invoke("info")
    assert decode(result.output.strip())["rows"] == 94


def test_schema_lists_all_columns(invoke, decode):
    result = invoke("info")
    names = [entry["column"] for entry in decode(result.output.strip())["schema"]]
    assert names == ["tourney_category", "tourney_level", "round", "round_of", "points"]


def test_schema_includes_dtypes(invoke, decode):
    result = invoke("info")
    dtypes = [entry["dtype"] for entry in decode(result.output.strip())["schema"]]
    assert dtypes == ["String", "String", "String", "Int32", "Int32"]


def test_preview_default_length(invoke, decode):
    result = invoke("info")
    assert len(decode(result.output.strip())["preview"]) == 2


@pytest.mark.parametrize("n", [1, 3, 50])
def test_preview_respects_n(invoke, decode, n):
    result = invoke("info", "-n", str(n))
    assert len(decode(result.output.strip())["preview"]) == min(n, 94)


def test_preview_row_has_correct_keys(invoke, decode):
    result = invoke("info", "-n", "1")
    row = decode(result.output.strip())["preview"][0]
    assert set(row.keys()) == {"tourney_category", "tourney_level", "round", "round_of", "points"}


def test_first_row_values(invoke, decode):
    result = invoke("info", "-n", "1")
    row = decode(result.output.strip())["preview"][0]
    assert row["tourney_category"] == "Grand Slam"
    assert row["tourney_level"] == "G2000"
    assert row["round"] == "F"
    assert row["round_of"] == 2
    assert row["points"] == 2000


def test_no_path_exits_with_error(runner, peek):
    result = runner.invoke(peek.app, ["info"])
    assert result.exit_code != 0


def test_nonexistent_file_exits_with_error(invoke):
    result = invoke("info", "--", "/nonexistent/file.parquet", use_fixture=False)
    assert result.exit_code != 0


def test_output_is_valid_toon(invoke, decode):
    result = invoke("info")
    parsed = decode(result.output.strip())
    assert set(parsed.keys()) == {"rows", "schema", "preview"}


def test_output_string(invoke):
    result = invoke("info")
    assert result.output == (
        "rows: 94\n"
        "schema[5]{column,dtype}:\n"
        "  tourney_category,String\n"
        "  tourney_level,String\n"
        "  round,String\n"
        "  round_of,Int32\n"
        "  points,Int32\n"
        "preview[2]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
    )
