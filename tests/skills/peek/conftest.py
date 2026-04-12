from __future__ import annotations

from typing import Any
from pathlib import Path

import pytest
from toon_format import decode as _decode

FIXTURE_PATH = Path(__file__).parent / "tourney_points.parquet"


@pytest.fixture(scope="session")
def peek(skill_loader):
    return skill_loader("peek")


@pytest.fixture(scope="session")
def fixture_path():
    return FIXTURE_PATH


@pytest.fixture
def invoke(run, peek, fixture_path):
    """Invoke the peek CLI app with default fixture path appended."""

    def _invoke(*args: str, use_fixture: bool = True, **kwargs):
        cmd = list(args)
        if use_fixture:
            cmd.append(str(fixture_path))
        return run(peek.app, cmd, **kwargs)

    return _invoke


@pytest.fixture
def decode():
    """Return a typed TOON decode helper."""

    def _fn(text: str) -> dict[str, Any]:
        result = _decode(text)
        assert isinstance(result, dict)
        return result

    return _fn
