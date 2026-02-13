"""Tests for mcpower_gui._resources — resource_path and _base_path."""

from pathlib import Path

from mcpower_gui._resources import _base_path, resource_path


class TestResources:
    def test_resource_path_returns_path(self):
        result = resource_path("cat.gif")
        assert isinstance(result, Path)

    def test_resource_path_cat_gif_exists(self):
        p = resource_path("cat.gif")
        assert p.exists(), f"Expected {p} to exist"

    def test_resource_path_icon_exists(self):
        p = resource_path("icon.png")
        assert p.exists(), f"Expected {p} to exist"

    def test_resource_path_acknowledgments_exists(self):
        p = resource_path("acknowledgments.txt")
        assert p.exists(), f"Expected {p} to exist"

    def test_base_path_returns_package_directory(self):
        base = _base_path()
        assert base.is_dir()
        assert (base / "__init__.py").exists()

    def test_resource_path_docs_subdir(self):
        p = resource_path("docs", "overview.md")
        assert isinstance(p, Path)
        assert p.exists(), f"Expected {p} to exist"
