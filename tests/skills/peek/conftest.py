from __future__ import annotations

import importlib.util
from typing import Any
from pathlib import Path

import pytest
from typer.testing import CliRunner
from toon_format import decode as _decode

SKILL_PATH = Path(__file__).resolve().parents[3] / "skills" / "peek" / "peek.py"
FIXTURE_PATH = Path(__file__).parent / "tourney_points.parquet"


def _load_peek():
    spec = importlib.util.spec_from_file_location("peek", SKILL_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def peek():
    return _load_peek()


@pytest.fixture(scope="session")
def fixture_path():
    return FIXTURE_PATH


@pytest.fixture(scope="session")
def sample_df(peek, fixture_path):
    return peek._read(fixture_path)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def invoke(runner, peek, fixture_path):
    """Invoke the peek CLI app with default fixture path appended."""

    def _invoke(*args: str, use_fixture: bool = True):
        cmd = list(args)
        if use_fixture:
            cmd.append(str(fixture_path))
        return runner.invoke(peek.app, cmd)

    return _invoke


@pytest.fixture
def decode():
    """Return a typed TOON decode helper."""

    def _fn(text: str) -> dict[str, Any]:
        result = _decode(text)
        assert isinstance(result, dict)
        return result

    return _fn
