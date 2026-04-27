"""Unit tests for the bump decision logic in scripts/release.py."""

import importlib.util
import sys
from pathlib import Path

import pytest

RELEASE_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release.py"


def _load_release_module():
    spec = importlib.util.spec_from_file_location("release", RELEASE_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["release"] = mod
    spec.loader.exec_module(mod)
    return mod


release = _load_release_module()


@pytest.mark.parametrize(
    "current,expected",
    [
        ("1.2.3", "none"),
        ("1.2.4", "patch"),
        ("1.3.0", "minor"),
        ("1.3.5", "minor"),
        ("2.0.0", "major"),
        ("2.5.7", "major"),
    ],
)
def test_diff_kind(current: str, expected: str) -> None:
    assert release.diff_kind("1.2.3", current) == expected


def test_diff_kind_below_base_raises() -> None:
    with pytest.raises(ValueError):
        release.diff_kind("1.2.3", "1.2.2")


def test_first_bump_minor_default() -> None:
    assert release.decide_bump("1.2.3", "1.2.3", "minor") == "1.3.0"


def test_first_bump_patch() -> None:
    assert release.decide_bump("1.2.3", "1.2.3", "patch") == "1.2.4"


def test_first_bump_major() -> None:
    assert release.decide_bump("1.2.3", "1.2.3", "major") == "2.0.0"


def test_no_double_patch() -> None:
    assert release.decide_bump("1.2.3", "1.2.4", "patch") is None


def test_no_double_minor() -> None:
    assert release.decide_bump("1.2.3", "1.3.0", "minor") is None


def test_no_double_major() -> None:
    assert release.decide_bump("1.2.3", "2.0.0", "major") is None


def test_higher_wins_patch_after_minor() -> None:
    assert release.decide_bump("1.2.3", "1.3.0", "patch") is None


def test_higher_wins_minor_after_major() -> None:
    assert release.decide_bump("1.2.3", "2.0.0", "minor") is None


def test_higher_wins_patch_after_major() -> None:
    assert release.decide_bump("1.2.3", "2.0.0", "patch") is None


def test_upgrade_patch_to_minor_resets_patch() -> None:
    assert release.decide_bump("1.2.3", "1.2.4", "minor") == "1.3.0"


def test_upgrade_patch_to_major_resets_all() -> None:
    assert release.decide_bump("1.2.3", "1.2.4", "major") == "2.0.0"


def test_upgrade_minor_to_major_resets_minor() -> None:
    assert release.decide_bump("1.2.3", "1.3.0", "major") == "2.0.0"


def test_upgrade_after_multi_step_minor_resets() -> None:
    """If a stale minor bump is several steps ahead, upgrading still anchors to base."""
    assert release.decide_bump("1.2.3", "1.5.0", "major") == "2.0.0"


def test_bump_semver() -> None:
    assert release.bump_semver("0.0.0", "patch") == "0.0.1"
    assert release.bump_semver("0.0.0", "minor") == "0.1.0"
    assert release.bump_semver("0.0.0", "major") == "1.0.0"
    assert release.bump_semver("9.9.9", "patch") == "9.9.10"
    assert release.bump_semver("9.9.9", "minor") == "9.10.0"
    assert release.bump_semver("9.9.9", "major") == "10.0.0"
