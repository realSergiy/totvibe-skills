"""Tests for peek extended modes: -c, -u, -g, -q, --cols, glob."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent


# --- Schema mode (-c) ---


def test_schema_mode(invoke):
    result = invoke("-c")
    assert result.output == (
        "tourney_points:\n"
        "  tourney_category: String\n"
        "  tourney_level: String\n"
        "  round: String\n"
        "  round_of: Int32\n"
        "  points: Int32\n"
        "rows: 94\n"
    )


# --- Unique mode (-u) ---


def test_unique_single_column(invoke):
    result = invoke("-u", "round")
    assert result.output == "round[11]: F,Q1,Q2,Q3,QF,R128,R16,R32,R64,RR,SF\n"


def test_unique_multiple_columns(invoke):
    result = invoke("-u", "round,tourney_category")
    assert result.output == (
        "round[11]: F,Q1,Q2,Q3,QF,R128,R16,R32,R64,RR,SF\n"
        "tourney_category[15]: ATP 1000 56D,ATP 1000 96D,ATP 250 32D,"
        "ATP 250 48D,ATP 500 32D,ATP 500 48D,ATP Finals,"
        "Challenger 100,Challenger 125,Challenger 175,"
        "Challenger 50,Challenger 75,Grand Slam,ITF M15,ITF M25\n"
    )


# --- Group-by mode (-g) ---


def test_groupby_single_column(invoke):
    result = invoke("-g", "round")
    assert result.output == (
        "group[11]{round,len}:\n"
        "  F,15\n"
        "  Q1,12\n"
        "  Q2,12\n"
        "  Q3,1\n"
        "  QF,14\n"
        "  R128,2\n"
        "  R16,14\n"
        "  R32,5\n"
        "  R64,3\n"
        "  RR,1\n"
        "  SF,15\n"
    )


def test_groupby_multiple_columns(invoke):
    result = invoke("-g", "tourney_category,round")
    assert result.output.startswith("group[94]{tourney_category,round,len}:\n")
    assert "  Grand Slam,F,1\n" in result.output


# --- SQL mode (-q) ---


def test_sql_groupby(invoke):
    result = invoke("-q", "SELECT round, COUNT(*) as cnt FROM t GROUP BY round ORDER BY cnt DESC, round")
    assert result.output == (
        "result[11]{round,cnt}:\n"
        "  F,15\n"
        "  SF,15\n"
        "  QF,14\n"
        "  R16,14\n"
        "  Q1,12\n"
        "  Q2,12\n"
        "  R32,5\n"
        "  R64,3\n"
        "  R128,2\n"
        "  Q3,1\n"
        "  RR,1\n"
    )


def test_sql_where(invoke):
    result = invoke("-q", "SELECT * FROM t WHERE tourney_category = 'Grand Slam'")
    assert result.output == (
        "result[10]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
        "  Grand Slam,G2000,QF,8,400\n"
        "  Grand Slam,G2000,R16,16,200\n"
        "  Grand Slam,G2000,R32,32,100\n"
        "  Grand Slam,G2000,R64,64,50\n"
        "  Grand Slam,G2000,R128,128,10\n"
        "  Grand Slam,G2000,Q3,160,30\n"
        "  Grand Slam,G2000,Q2,192,16\n"
        "  Grand Slam,G2000,Q1,256,8\n"
    )


def test_sql_limit(invoke):
    result = invoke("-q", "SELECT * FROM t LIMIT 3")
    assert result.output == (
        "result[3]{tourney_category,tourney_level,round,round_of,points}:\n"
        "  Grand Slam,G2000,F,2,2000\n"
        "  Grand Slam,G2000,SF,4,800\n"
        "  Grand Slam,G2000,QF,8,400\n"
    )


# --- Multi-file SQL mode ---


def test_sql_multi_file_t1_t2(runner, peek):
    """Multiple files are registered as t1, t2 for cross-file queries."""
    players = str(FIXTURE_DIR / "players.parquet")
    points = str(FIXTURE_DIR / "tourney_points.parquet")
    result = runner.invoke(
        peek.app,
        ["-q", "SELECT t1.player, t1.wins FROM t1 ORDER BY t1.wins DESC", players, points],
    )
    assert result.exit_code == 0
    assert result.output == (
        "result[3]{player,wins}:\n"
        "  Federer,103\n"
        "  Djokovic,98\n"
        "  Nadal,92\n"
    )


def test_sql_multi_file_cross_join(runner, peek):
    """Cross-file query joining t1 and t2."""
    players = str(FIXTURE_DIR / "players.parquet")
    points = str(FIXTURE_DIR / "tourney_points.parquet")
    result = runner.invoke(
        peek.app,
        [
            "-q",
            "SELECT COUNT(*) as cnt FROM t1 CROSS JOIN t2",
            players,
            points,
        ],
    )
    assert result.exit_code == 0
    assert "cnt" in result.output
    assert "282" in result.output  # 3 players × 94 point rows


def test_sql_single_file_t1_alias(invoke):
    """Single file is accessible as both t and t1."""
    result = invoke("-q", "SELECT COUNT(*) as cnt FROM t1")
    assert result.exit_code == 0
    assert "94" in result.output


# --- Column selection (--cols) ---


def test_cols_select(invoke):
    result = invoke("--cols", "round,points")
    assert result.output == (
        "tourney_points[2]{round,points}:\n"
        "  F,2000\n"
        "  SF,800\n"
        "rows: 94\n"
    )


def test_cols_with_n(invoke):
    result = invoke("--cols", "round,points", "-n", "5")
    assert result.output == (
        "tourney_points[5]{round,points}:\n"
        "  F,2000\n"
        "  SF,800\n"
        "  QF,400\n"
        "  R16,200\n"
        "  R32,100\n"
        "rows: 94\n"
    )


def test_cols_with_types(invoke):
    result = invoke("--cols", "round,points", "-t")
    assert result.output == (
        "tourney_points[2]{round,points}:\n"
        "  F,2000\n"
        "  SF,800\n"
        "types[2]: String,Int32\n"
        "rows: 94\n"
    )


def test_cols_with_all_rows(invoke, decode):
    result = invoke("--cols", "round", "-a")
    parsed = decode(result.output.strip())
    assert len(parsed["tourney_points"]) == 94
    assert "rows" not in parsed


# --- Glob support ---


def test_glob_schema_multiple(runner, peek):
    pattern = str(FIXTURE_DIR / "*.parquet")
    result = runner.invoke(peek.app, ["-c", pattern])
    assert result.output == (
        "players:\n"
        "  player: String\n"
        "  wins: Int64\n"
        "  surface: String\n"
        "rows: 3\n"
        "\n"
        "tourney_points:\n"
        "  tourney_category: String\n"
        "  tourney_level: String\n"
        "  round: String\n"
        "  round_of: Int32\n"
        "  points: Int32\n"
        "rows: 94\n"
    )


def test_glob_preview_multiple(runner, peek):
    pattern = str(FIXTURE_DIR / "*.parquet")
    result = runner.invoke(peek.app, [pattern])
    assert result.exit_code == 0
    blocks = result.output.strip().split("\n\n")
    assert len(blocks) == 2
    assert blocks[0].startswith("players[2]")
    assert blocks[1].startswith("tourney_points[2]")


def test_glob_no_match(runner, peek):
    result = runner.invoke(peek.app, ["/nonexistent/*.parquet"])
    assert result.exit_code != 0


# --- Mode exclusivity ---


@pytest.mark.parametrize(
    "args",
    [
        ("-c", "-u", "round"),
        ("-c", "-g", "round"),
        ("-c", "-q", "SELECT * FROM t"),
        ("-u", "round", "-g", "round"),
    ],
    ids=["c+u", "c+g", "c+q", "u+g"],
)
def test_mode_conflict(invoke, args):
    result = invoke(*args, expect_error=True)
    assert result.exit_code != 0
