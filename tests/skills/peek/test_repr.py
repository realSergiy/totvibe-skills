"""Integration tests for the peek repr command."""

from __future__ import annotations

import polars as pl


def test_exits_successfully(invoke):
    result = invoke("repr")
    assert result.exit_code == 0


def test_output_contains_dataframe_constructor(invoke, decode):
    result = invoke("repr", "-n", "2")
    assert "pl.DataFrame" in decode(result.output.strip())["constructor"]


def test_constructor_is_executable(invoke, decode):
    result = invoke("repr", "-n", "2")
    df = eval(decode(result.output.strip())["constructor"])  # noqa: S307
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 5)


def test_respects_n(invoke, decode):
    result = invoke("repr", "-n", "3")
    df = eval(decode(result.output.strip())["constructor"])  # noqa: S307
    assert df.shape[0] == 3


def test_output_string(invoke):
    result = invoke("repr", "-n", "2")
    assert result.output == (
        'constructor: "pl.DataFrame(\\n'
        "    [\\n"
        "        pl.Series('tourney_category', ['Grand Slam', 'Grand Slam'], dtype=pl.String),\\n"
        "        pl.Series('tourney_level', ['G2000', 'G2000'], dtype=pl.String),\\n"
        "        pl.Series('round', ['F', 'SF'], dtype=pl.String),\\n"
        "        pl.Series('round_of', [2, 4], dtype=pl.Int32),\\n"
        "        pl.Series('points', [2000, 800], dtype=pl.Int32),\\n"
        "    ]\\n"
        ')\\n"\n'
    )
