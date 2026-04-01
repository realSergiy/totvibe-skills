"""Integration tests for the peek head command."""

from __future__ import annotations

import pytest


def test_exits_successfully(invoke):
    result = invoke("head")
    assert result.exit_code == 0


def test_default_row_count(invoke, decode):
    result = invoke("head")
    assert len(decode(result.output.strip())["rows"]) == 2


@pytest.mark.parametrize("n", [1, 5, 50])
def test_respects_n(invoke, decode, n):
    result = invoke("head", "-n", str(n))
    assert len(decode(result.output.strip())["rows"]) == min(n, 94)


def test_row_has_correct_keys(invoke, decode):
    result = invoke("head", "-n", "1")
    assert set(decode(result.output.strip())["rows"][0].keys()) == {
        "tourney_category", "tourney_level", "round", "round_of", "points",
    }


def test_first_row_values(invoke, decode):
    result = invoke("head", "-n", "1")
    row = decode(result.output.strip())["rows"][0]
    assert row["tourney_category"] == "Grand Slam"
    assert row["points"] == 2000


def test_output_is_valid_toon(invoke, decode):
    result = invoke("head", "-n", "2")
    parsed = decode(result.output.strip())
    assert "rows" in parsed


def test_output_string(invoke):
    result = invoke("head", "-n", "2")
    assert result.output == (
        "rows[2]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
    )
