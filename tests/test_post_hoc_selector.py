"""Tests for PostHocSelector widget."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from mcpower_gui.widgets.post_hoc_selector import PostHocSelector

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def selector():
    widget = PostHocSelector()
    yield widget
    widget.deleteLater()


# ---------------------------------------------------------------------------
# set_factors: pairwise combination generation
# ---------------------------------------------------------------------------


class TestSetFactors:
    """Tests for set_factors() checkbox generation from factor definitions."""

    def test_single_factor_two_levels(self, selector):
        """Factor with 2 levels produces exactly 1 pairwise comparison."""
        selector.set_factors({"group": 2})
        assert len(selector._checkboxes) == 1
        names = [name for name, _ in selector._checkboxes]
        assert names == ["group[1] vs group[2]"]

    def test_single_factor_three_levels(self, selector):
        """Factor with 3 levels produces C(3,2) = 3 comparisons."""
        selector.set_factors({"condition": 3})
        names = [name for name, _ in selector._checkboxes]
        assert len(names) == 3
        assert "condition[1] vs condition[2]" in names
        assert "condition[1] vs condition[3]" in names
        assert "condition[2] vs condition[3]" in names

    def test_single_factor_four_levels(self, selector):
        """Factor with 4 levels produces C(4,2) = 6 comparisons."""
        selector.set_factors({"treatment": 4})
        assert len(selector._checkboxes) == 6

    def test_factor_with_one_level_skipped(self, selector):
        """Factor with fewer than 2 levels produces no checkboxes."""
        selector.set_factors({"single": 1})
        assert len(selector._checkboxes) == 0

    def test_factor_with_zero_levels_skipped(self, selector):
        """Factor with 0 levels produces no checkboxes."""
        selector.set_factors({"empty": 0})
        assert len(selector._checkboxes) == 0

    def test_empty_factors_dict(self, selector):
        """Empty dict produces no checkboxes."""
        selector.set_factors({})
        assert len(selector._checkboxes) == 0

    def test_multiple_factors_generates_combinations_for_each(self, selector):
        """Two factors each produce their own pairwise comparisons."""
        selector.set_factors({"A": 2, "B": 3})
        names = [name for name, _ in selector._checkboxes]
        # A with 2 levels: 1 comparison; B with 3 levels: 3 comparisons
        assert len(names) == 4
        assert "A[1] vs A[2]" in names
        assert "B[1] vs B[2]" in names
        assert "B[1] vs B[3]" in names
        assert "B[2] vs B[3]" in names

    def test_multi_factor_adds_section_labels(self, selector):
        """Multiple factors produce bold QLabel section headers."""
        selector.set_factors({"alpha": 2, "beta": 2})
        # Inspect the layout for QLabel widgets
        labels = []
        for i in range(selector._layout.count()):
            w = selector._layout.itemAt(i).widget()
            if isinstance(w, QLabel):
                labels.append(w.text())
        assert "alpha:" in labels
        assert "beta:" in labels

    def test_single_factor_no_section_label(self, selector):
        """A single factor does not produce a section label."""
        selector.set_factors({"only": 3})
        labels = []
        for i in range(selector._layout.count()):
            w = selector._layout.itemAt(i).widget()
            if isinstance(w, QLabel):
                labels.append(w.text())
        assert len(labels) == 0

    def test_rebuild_clears_old_checkboxes(self, selector):
        """Calling set_factors again replaces previous checkboxes."""
        selector.set_factors({"old": 3})
        assert len(selector._checkboxes) == 3
        selector.set_factors({"new": 2})
        assert len(selector._checkboxes) == 1
        names = [name for name, _ in selector._checkboxes]
        assert "new[1] vs new[2]" in names
        assert not any("old" in name for name in names)

    def test_all_checkboxes_start_unchecked(self, selector):
        """All newly created checkboxes are unchecked by default."""
        selector.set_factors({"group": 4})
        for _, cb in selector._checkboxes:
            assert not cb.isChecked()

    def test_select_all_resets_to_unchecked_on_set_factors(self, selector):
        """After set_factors(), the Select All checkbox is Unchecked."""
        selector.set_factors({"group": 3})
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked

    def test_factors_sorted_alphabetically(self, selector):
        """Factors are processed in alphabetical order."""
        selector.set_factors({"zebra": 2, "apple": 2})
        names = [name for name, _ in selector._checkboxes]
        # apple before zebra
        assert names[0].startswith("apple")
        assert names[1].startswith("zebra")

    def test_mixed_valid_and_skipped_factors(self, selector):
        """Factors with <2 levels are silently skipped alongside valid ones."""
        selector.set_factors({"skip": 1, "keep": 3})
        names = [name for name, _ in selector._checkboxes]
        assert len(names) == 3
        assert all("keep" in n for n in names)
        assert not any("skip" in n for n in names)


# ---------------------------------------------------------------------------
# get_selected: retrieval of checked comparisons
# ---------------------------------------------------------------------------


class TestGetSelected:
    """Tests for get_selected() return values."""

    def test_empty_when_none_checked(self, selector):
        """No checked boxes => empty list."""
        selector.set_factors({"group": 3})
        assert selector.get_selected() == []

    def test_returns_checked_items(self, selector):
        """Checking specific boxes returns their comparison strings."""
        selector.set_factors({"group": 3})
        # Check the first and third comparisons
        selector._checkboxes[0][1].setChecked(True)
        selector._checkboxes[2][1].setChecked(True)
        selected = selector.get_selected()
        assert len(selected) == 2
        assert selector._checkboxes[0][0] in selected
        assert selector._checkboxes[2][0] in selected

    def test_returns_all_when_all_checked(self, selector):
        """All checked => all comparison strings returned."""
        selector.set_factors({"group": 3})
        for _, cb in selector._checkboxes:
            cb.setChecked(True)
        selected = selector.get_selected()
        assert len(selected) == 3

    def test_order_matches_checkbox_order(self, selector):
        """Selected items maintain the order of the checkboxes."""
        selector.set_factors({"group": 4})
        # Check all
        for _, cb in selector._checkboxes:
            cb.setChecked(True)
        selected = selector.get_selected()
        expected = [name for name, _ in selector._checkboxes]
        assert selected == expected

    def test_empty_when_no_factors(self, selector):
        """get_selected on widget with no factors returns empty list."""
        assert selector.get_selected() == []

    def test_unchecking_removes_from_selected(self, selector):
        """Unchecking a previously checked box removes it from results."""
        selector.set_factors({"group": 2})
        selector._checkboxes[0][1].setChecked(True)
        assert len(selector.get_selected()) == 1
        selector._checkboxes[0][1].setChecked(False)
        assert selector.get_selected() == []


# ---------------------------------------------------------------------------
# _on_select_all: check/uncheck all items
# ---------------------------------------------------------------------------


class TestSelectAll:
    """Tests for the Select All checkbox behavior."""

    def test_select_all_checks_all_items(self, selector):
        """Setting Select All to Checked checks every comparison checkbox."""
        selector.set_factors({"group": 3})
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        for _, cb in selector._checkboxes:
            assert cb.isChecked()

    def test_uncheck_all_unchecks_all_items(self, selector):
        """Setting Select All to Unchecked unchecks every comparison checkbox."""
        selector.set_factors({"group": 3})
        # First check all
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        # Then uncheck all
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        for _, cb in selector._checkboxes:
            assert not cb.isChecked()

    def test_select_all_then_get_selected(self, selector):
        """After Select All, get_selected returns all comparisons."""
        selector.set_factors({"group": 3})
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        selected = selector.get_selected()
        assert len(selected) == 3

    def test_select_all_with_no_checkboxes(self, selector):
        """Toggling Select All with no checkboxes does not raise."""
        selector.set_factors({})
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        assert selector.get_selected() == []

    def test_select_all_partial_does_not_change_items(self, selector):
        """Setting Select All to PartiallyChecked does not check or uncheck items.

        The _on_select_all handler only acts on Checked state, so
        PartiallyChecked does not modify individual checkboxes.
        """
        selector.set_factors({"group": 3})
        selector._checkboxes[0][1].setChecked(True)
        selector._select_all.setCheckState(Qt.CheckState.PartiallyChecked)
        # The one checked item stays checked, others stay unchecked
        assert selector._checkboxes[0][1].isChecked()
        assert not selector._checkboxes[1][1].isChecked()
        assert not selector._checkboxes[2][1].isChecked()


# ---------------------------------------------------------------------------
# _on_item_changed: tri-state logic
# ---------------------------------------------------------------------------


class TestTriState:
    """Tests for tri-state Select All driven by individual checkbox changes."""

    def test_all_checked_sets_checked(self, selector):
        """Checking all items sets Select All to Checked."""
        selector.set_factors({"group": 3})
        for _, cb in selector._checkboxes:
            cb.setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_none_checked_sets_unchecked(self, selector):
        """When no items are checked, Select All is Unchecked."""
        selector.set_factors({"group": 3})
        # All start unchecked
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked

    def test_some_checked_sets_partial(self, selector):
        """Checking some (but not all) items sets Select All to PartiallyChecked."""
        selector.set_factors({"group": 3})
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked

    def test_uncheck_one_from_all_sets_partial(self, selector):
        """Unchecking one item from a fully checked set triggers PartiallyChecked."""
        selector.set_factors({"group": 3})
        # Check all via Select All
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        # Uncheck one item
        selector._checkboxes[1][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked

    def test_check_last_item_transitions_to_checked(self, selector):
        """Checking the final unchecked item transitions Select All to Checked."""
        selector.set_factors({"group": 2})
        # Only 1 comparison: check it
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_uncheck_last_item_transitions_to_unchecked(self, selector):
        """Unchecking the only checked item transitions to Unchecked."""
        selector.set_factors({"group": 2})
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        selector._checkboxes[0][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked

    def test_partial_with_multiple_factors(self, selector):
        """Tri-state works correctly across comparisons from multiple factors."""
        selector.set_factors({"A": 2, "B": 2})
        assert len(selector._checkboxes) == 2
        # Check only one
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked
        # Check the other
        selector._checkboxes[1][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_rapid_toggle_maintains_consistency(self, selector):
        """Rapid check/uncheck cycles keep tri-state consistent."""
        selector.set_factors({"group": 3})
        for _, cb in selector._checkboxes:
            cb.setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        # Uncheck middle
        selector._checkboxes[1][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked
        # Recheck middle
        selector._checkboxes[1][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        # Uncheck all one by one
        for _, cb in selector._checkboxes:
            cb.setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked


# ---------------------------------------------------------------------------
# has_any_factors: presence check
# ---------------------------------------------------------------------------


class TestHasAnyFactors:
    """Tests for has_any_factors() boolean check."""

    def test_false_on_init(self, selector):
        """Before any set_factors call, has_any_factors is False."""
        assert selector.has_any_factors() is False

    def test_true_after_valid_factor(self, selector):
        """After setting a factor with >=2 levels, has_any_factors is True."""
        selector.set_factors({"group": 3})
        assert selector.has_any_factors() is True

    def test_false_after_single_level_factor(self, selector):
        """A factor with 1 level produces no checkboxes => False."""
        selector.set_factors({"single": 1})
        assert selector.has_any_factors() is False

    def test_false_after_empty_factors(self, selector):
        """Empty factors dict => False."""
        selector.set_factors({})
        assert selector.has_any_factors() is False

    def test_true_with_multiple_factors(self, selector):
        """Multiple valid factors => True."""
        selector.set_factors({"A": 2, "B": 3})
        assert selector.has_any_factors() is True

    def test_false_after_clearing(self, selector):
        """Setting factors then clearing them returns False."""
        selector.set_factors({"group": 3})
        assert selector.has_any_factors() is True
        selector.set_factors({})
        assert selector.has_any_factors() is False

    def test_true_when_mixed_valid_and_invalid(self, selector):
        """At least one valid factor among invalid ones => True."""
        selector.set_factors({"skip": 0, "valid": 2})
        assert selector.has_any_factors() is True

    def test_false_when_all_invalid(self, selector):
        """All factors with <2 levels => False."""
        selector.set_factors({"a": 1, "b": 0, "c": 1})
        assert selector.has_any_factors() is False
