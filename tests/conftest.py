"""Shared pytest configuration for mcpower-gui tests."""

import os
import sys

import pytest

# Must be set before any Qt import so Qt uses the offscreen (headless) platform.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication shared across all GUI tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    yield app
