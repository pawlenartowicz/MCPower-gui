"""Tests for ClusterEditor widget."""

import pytest
from PySide6.QtWidgets import QApplication

from mcpower_gui.widgets.cluster_editor import ClusterEditor

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def editor():
    widget = ClusterEditor()
    yield widget
    widget.deleteLater()


class TestClusterEditorEmpty:
    def test_empty_on_init(self, editor):
        assert editor.get_cluster_configs() == []

    def test_no_random_effects(self, editor):
        editor.set_random_effects([], ["x1", "x2"])
        assert editor.get_cluster_configs() == []


class TestClusterEditorRandomIntercept:
    def test_single_intercept(self, editor):
        re = [{"type": "random_intercept", "grouping_var": "school"}]
        editor.set_random_effects(re, ["x1"])
        configs = editor.get_cluster_configs()
        assert len(configs) == 1
        assert configs[0]["grouping_var"] == "school"
        assert "ICC" in configs[0]
        assert "n_clusters" in configs[0]
        assert configs[0]["ICC"] == 0.2  # default
        assert configs[0]["n_clusters"] == 20  # default

    def test_two_independent_intercepts(self, editor):
        re = [
            {"type": "random_intercept", "grouping_var": "school"},
            {"type": "random_intercept", "grouping_var": "region"},
        ]
        editor.set_random_effects(re, ["x1"])
        configs = editor.get_cluster_configs()
        assert len(configs) == 2
        grouping_vars = {c["grouping_var"] for c in configs}
        assert grouping_vars == {"school", "region"}


class TestClusterEditorRandomSlope:
    def test_slope_fields(self, editor):
        re = [{"type": "random_slope", "grouping_var": "school",
               "slope_vars": ["x1"]}]
        editor.set_random_effects(re, ["x1"])
        configs = editor.get_cluster_configs()
        assert len(configs) == 1
        cfg = configs[0]
        assert cfg["grouping_var"] == "school"
        assert cfg["random_slopes"] == ["x1"]
        assert "slope_variance" in cfg
        assert "slope_intercept_corr" in cfg


class TestClusterEditorNested:
    def test_nested_produces_parent_and_child(self, editor):
        re = [
            {"type": "random_intercept", "grouping_var": "school"},
            {"type": "random_intercept", "grouping_var": "school:classroom",
             "parent_var": "school"},
        ]
        editor.set_random_effects(re, ["x1"])
        configs = editor.get_cluster_configs()
        assert len(configs) == 2
        parent = [c for c in configs if c["grouping_var"] == "school"][0]
        child = [c for c in configs if c["grouping_var"] == "school:classroom"][0]
        assert "n_clusters" in parent
        assert "n_per_parent" in child
        assert "n_clusters" not in child


class TestClusterEditorSignals:
    def test_clusters_changed_emitted_on_set(self, editor):
        """clusters_changed emitted when set_random_effects is called."""
        results = []
        editor.clusters_changed.connect(lambda configs: results.append(configs))
        re = [{"type": "random_intercept", "grouping_var": "school"}]
        editor.set_random_effects(re, ["x1"])
        assert len(results) >= 1
        assert results[-1][0]["grouping_var"] == "school"


class TestClusterEditorPreservesValues:
    def test_values_preserved_on_rebuild(self, editor):
        """When formula changes but same random effect exists, preserve values."""
        re = [{"type": "random_intercept", "grouping_var": "school"}]
        editor.set_random_effects(re, ["x1"])
        configs = editor.get_cluster_configs()
        assert configs[0]["ICC"] == 0.2  # default

        # Simulate user changing ICC via the spinbox
        editor._cards[0]._icc_spin.setValue(0.35)
        configs = editor.get_cluster_configs()
        assert configs[0]["ICC"] == 0.35

        # Rebuild with same random effect — should preserve value
        editor.set_random_effects(re, ["x1", "x2"])
        configs = editor.get_cluster_configs()
        assert configs[0]["ICC"] == 0.35
