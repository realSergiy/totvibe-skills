"""Integration tests for the peek CLI."""

from __future__ import annotations

import pytest


def test_default_output(invoke):
    result = invoke()
    assert result.output == (
        "tourney_points[2]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
        "rows: 94\n"
    )


def test_n_1(invoke):
    result = invoke("-n", "1")
    assert result.output == (
        "tourney_points[1]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "rows: 94\n"
    )


def test_n_5(invoke):
    result = invoke("-n", "5")
    assert result.output == (
        "tourney_points[5]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
        "  Grand Slam,G2000,QF,8,400\n"
        "  Grand Slam,G2000,R16,16,200\n"
        "  Grand Slam,G2000,R32,32,100\n"
        "rows: 94\n"
    )


@pytest.mark.parametrize("n", [3, 50])
def test_preview_respects_n(invoke, decode, n):
    result = invoke("-n", str(n))
    assert len(decode(result.output.strip())["tourney_points"]) == min(n, 94)


@pytest.mark.parametrize("n", [94, 200], ids=["exact", "overshoot"])
def test_n_gte_total_hides_rows(invoke, n):
    result = invoke("-n", str(n))
    assert "rows" not in result.output


def test_types_flag(invoke):
    result = invoke("-t")
    assert result.output == (
        "tourney_points[2]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
        "types[5]: String,String,String,Int32,Int32\n"
        "rows: 94\n"
    )


def test_all_rows_no_row_count(invoke, decode):
    result = invoke("-a")
    parsed = decode(result.output.strip())
    assert len(parsed["tourney_points"]) == 94
    assert "rows" not in parsed


def test_no_path_exits_with_error(runner, peek):
    result = runner.invoke(peek.app, [])
    assert result.exit_code != 0


def test_nonexistent_file_exits_with_error(invoke):
    result = invoke("--", "/nonexistent/file.parquet", use_fixture=False, expect_error=True)
    assert result.exit_code != 0
