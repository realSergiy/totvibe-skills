from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from typer.testing import CliRunner

SKILL_PATH = Path(__file__).resolve().parents[3] / "skills" / "suggest" / "suggest.py"


def _load_suggest():
    spec = importlib.util.spec_from_file_location("suggest", SKILL_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def suggest():
    return _load_suggest()


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def invoke(runner, suggest):
    """Invoke the suggest CLI app."""

    def _invoke(*args: str):
        return runner.invoke(suggest.app, list(args))

    return _invoke
