"""Common CLI tests for all skills.

Auto-discovers every skill and verifies shared CLI conventions:
--help, --version, and version consistency across all three locations.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SKILL_NAMES = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


@pytest.fixture(params=[pytest.param(n, id=n) for n in SKILL_NAMES])
def skill(request, skill_loader):
    return skill_loader(request.param)


def test_help(skill, runner):
    result = runner.invoke(skill.app, ["--help"])
    assert result.exit_code == 0


def test_version(skill, runner):
    result = runner.invoke(skill.app, ["--version"])
    assert result.exit_code == 0
    assert skill.__version__ in result.output


def _skill_md_version(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text()
    m = re.search(r'version:\s*"(.+?)"', text)
    return m.group(1) if m else ""


def test_version_consistent(skill, runner):
    skill_dir = SKILLS_DIR / skill.__name__
    py_version = skill.__version__
    md_version = _skill_md_version(skill_dir)
    pkg_version = json.loads((skill_dir / "package.json").read_text())["version"]
    assert py_version == md_version, f"__version__ ({py_version}) != SKILL.md ({md_version})"
    assert py_version == pkg_version, f"__version__ ({py_version}) != package.json ({pkg_version})"
