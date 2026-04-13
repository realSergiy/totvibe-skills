from __future__ import annotations

from pathlib import Path

import pytest

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
