"""Tests for package version consistency."""

from __future__ import annotations

import re
from pathlib import Path

from csv2vcard import __version__


def test_version_matches_pyproject() -> None:
    """Test that __version__ and pyproject.toml agree (the release workflow checks both)."""
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "(.+?)"', pyproject, re.MULTILINE)

    assert match is not None
    assert match[1] == __version__
