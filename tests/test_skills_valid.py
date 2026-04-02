"""Validate every skill in the repo against the Agent Skills spec."""

from pathlib import Path

import pytest
from skills_ref import read_properties, validate

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
SKILL_DIRS = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


@pytest.fixture(params=[pytest.param(d, id=d.name) for d in SKILL_DIRS])
def skill_dir(request: pytest.FixtureRequest) -> Path:
    return request.param


def test_skill_validates(skill_dir: Path) -> None:
    errors = validate(skill_dir)
    assert errors == [], f"Validation errors in {skill_dir.name}: {errors}"


def test_skill_has_required_properties(skill_dir: Path) -> None:
    props = read_properties(skill_dir)
    assert props.name, "name must be non-empty"
    assert props.description, "description must be non-empty"
