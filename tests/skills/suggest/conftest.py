from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def suggest(skill_loader):
    return skill_loader("suggest")


@pytest.fixture(autouse=True)
def suggest_dir(suggest, tmp_path):
    """Redirect SKILL_SUGGEST_DIR to tmp_path for test isolation.

    In production, the directory is configured via the SKILL_SUGGEST_DIR env var
    (defaulting to ~/Documents/skill-suggestions). Tests override the module
    attribute directly for simplicity.
    """
    original = suggest.SKILL_SUGGEST_DIR
    suggest.SKILL_SUGGEST_DIR = tmp_path
    yield tmp_path
    suggest.SKILL_SUGGEST_DIR = original


@pytest.fixture
def invoke(run, suggest):
    """Invoke the suggest CLI app."""

    def _invoke(*args: str, **kwargs):
        return run(suggest.app, args, **kwargs)

    return _invoke
