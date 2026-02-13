"""Frozen-safe resource loading for PyInstaller bundles."""

from __future__ import annotations

import sys
from pathlib import Path


def _base_path() -> Path:
    """Return the base path for package resources.

    In a PyInstaller bundle ``sys._MEIPASS`` points to the temporary
    extraction directory.  Otherwise, fall back to the installed package
    location.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass) / "mcpower_gui"
    # Normal (non-frozen) install — package directory
    return Path(__file__).resolve().parent


def resource_path(*parts: str) -> Path:
    """Return the absolute path to a package resource file.

    Usage::

        resource_path("cat.gif")
        resource_path("docs", "overview.md")
        resource_path("acknowledgments.txt")
    """
    return _base_path().joinpath(*parts)
