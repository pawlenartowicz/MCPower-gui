"""Tests for TargetTestSelector widget."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox

from mcpower_gui.widgets.target_test_selector import (
    TargetTestSelector,
    _MAX_HEIGHT,
    _PADDING,
    _ROW_HEIGHT,
)

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def selector():
    widget = TargetTestSelector()
    yield widget
    widget.deleteLater()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestInitialState:
    """Tests for the widget's state immediately after construction."""

    def test_no_checkboxes_on_init(self, selector):
        """Before set_tests(), the internal checkbox list is empty."""
        assert len(selector._checkboxes) == 0

    def test_select_all_checked_on_init(self, selector):
        """Select All starts as Checked before any tests are loaded."""
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_select_all_is_tristate(self, selector):
        """Select All is configured for tristate operation."""
        assert selector._select_all.isTristate()

    def test_get_value_returns_all_when_empty(self, selector):
        """With no checkboxes, all are 'selected' (vacuously), so get_value returns 'all'."""
        assert selector.get_value() == "all"


# ---------------------------------------------------------------------------
# set_tests: checkbox creation
# ---------------------------------------------------------------------------


class TestSetTests:
    """Tests for set_tests() checkbox generation."""

    def test_creates_correct_number_of_checkboxes(self, selector):
        """set_tests() creates one checkbox per test name."""
        selector.set_tests(["t-test", "ANOVA", "chi-square"])
        assert len(selector._checkboxes) == 3

    def test_checkbox_names_match_input(self, selector):
        """Created checkboxes have names matching the input test list."""
        tests = ["t-test", "ANOVA", "chi-square"]
        selector.set_tests(tests)
        names = [name for name, _ in selector._checkboxes]
        assert names == tests

    def test_all_checkboxes_checked_by_default(self, selector):
        """All newly created checkboxes are checked by default."""
        selector.set_tests(["t-test", "ANOVA", "chi-square"])
        for _, cb in selector._checkboxes:
            assert cb.isChecked()

    def test_select_all_checked_after_set_tests(self, selector):
        """After set_tests(), Select All is in Checked state."""
        selector.set_tests(["t-test", "ANOVA"])
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_single_test(self, selector):
        """set_tests() works correctly with a single test."""
        selector.set_tests(["only-one"])
        assert len(selector._checkboxes) == 1
        name, cb = selector._checkboxes[0]
        assert name == "only-one"
        assert cb.isChecked()

    def test_empty_list_clears_checkboxes(self, selector):
        """set_tests([]) results in no checkboxes."""
        selector.set_tests(["a", "b"])
        assert len(selector._checkboxes) == 2
        selector.set_tests([])
        assert len(selector._checkboxes) == 0

    def test_rebuild_replaces_old_checkboxes(self, selector):
        """Calling set_tests() again replaces previous checkboxes entirely."""
        selector.set_tests(["old1", "old2", "old3"])
        assert len(selector._checkboxes) == 3
        selector.set_tests(["new1", "new2"])
        assert len(selector._checkboxes) == 2
        names = [name for name, _ in selector._checkboxes]
        assert names == ["new1", "new2"]
        assert not any("old" in name for name in names)

    def test_rebuild_resets_select_all_to_checked(self, selector):
        """After rebuilding, Select All is reset to Checked regardless of prior state."""
        selector.set_tests(["a", "b", "c"])
        # Manually uncheck one to make Select All partial
        selector._checkboxes[0][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked
        # Rebuild
        selector.set_tests(["x", "y"])
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_checkboxes_are_qcheckbox_instances(self, selector):
        """Each checkbox in the internal list is a QCheckBox widget."""
        selector.set_tests(["a", "b"])
        for _, cb in selector._checkboxes:
            assert isinstance(cb, QCheckBox)

    def test_checkboxes_added_to_layout(self, selector):
        """Checkboxes are added to the internal scroll layout."""
        selector.set_tests(["a", "b", "c"])
        assert selector._layout.count() == 3


# ---------------------------------------------------------------------------
# get_value: return value logic
# ---------------------------------------------------------------------------


class TestGetValue:
    """Tests for get_value() return values."""

    def test_all_checked_returns_all(self, selector):
        """When all checkboxes are checked, get_value returns 'all'."""
        selector.set_tests(["t-test", "ANOVA", "chi-square"])
        assert selector.get_value() == "all"

    def test_subset_returns_comma_separated(self, selector):
        """When only some are checked, get_value returns comma-separated names."""
        selector.set_tests(["t-test", "ANOVA", "chi-square"])
        selector._checkboxes[1][1].setChecked(False)  # Uncheck ANOVA
        result = selector.get_value()
        assert result == "t-test, chi-square"

    def test_single_checked_returns_name(self, selector):
        """When only one is checked, get_value returns just that name."""
        selector.set_tests(["t-test", "ANOVA", "chi-square"])
        selector._checkboxes[0][1].setChecked(False)
        selector._checkboxes[2][1].setChecked(False)
        assert selector.get_value() == "ANOVA"

    def test_none_checked_returns_empty_string(self, selector):
        """When no checkboxes are checked, get_value returns an empty string."""
        selector.set_tests(["t-test", "ANOVA"])
        selector._checkboxes[0][1].setChecked(False)
        selector._checkboxes[1][1].setChecked(False)
        assert selector.get_value() == ""

    def test_order_matches_input_order(self, selector):
        """Selected items maintain the order of the original test list."""
        selector.set_tests(["alpha", "beta", "gamma", "delta"])
        selector._checkboxes[1][1].setChecked(False)  # Uncheck beta
        result = selector.get_value()
        assert result == "alpha, gamma, delta"

    def test_get_value_after_recheck_returns_all(self, selector):
        """Unchecking then rechecking all returns 'all' again."""
        selector.set_tests(["a", "b"])
        selector._checkboxes[0][1].setChecked(False)
        assert selector.get_value() != "all"
        selector._checkboxes[0][1].setChecked(True)
        assert selector.get_value() == "all"

    def test_no_tests_returns_all(self, selector):
        """With no tests set, get_value returns 'all' (vacuously true)."""
        selector.set_tests([])
        assert selector.get_value() == "all"


# ---------------------------------------------------------------------------
# _on_select_all: check/uncheck all items
# ---------------------------------------------------------------------------


class TestSelectAll:
    """Tests for the Select All checkbox behavior."""

    def test_uncheck_all_unchecks_every_item(self, selector):
        """Setting Select All to Unchecked unchecks every test checkbox."""
        selector.set_tests(["a", "b", "c"])
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        for _, cb in selector._checkboxes:
            assert not cb.isChecked()

    def test_check_all_checks_every_item(self, selector):
        """Setting Select All to Checked checks every test checkbox."""
        selector.set_tests(["a", "b", "c"])
        # First uncheck all
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        for _, cb in selector._checkboxes:
            assert not cb.isChecked()
        # Then check all
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        for _, cb in selector._checkboxes:
            assert cb.isChecked()

    def test_select_all_then_get_value(self, selector):
        """After Select All => Checked, get_value returns 'all'."""
        selector.set_tests(["a", "b", "c"])
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        assert selector.get_value() == "all"

    def test_deselect_all_then_get_value(self, selector):
        """After Select All => Unchecked, get_value returns empty string."""
        selector.set_tests(["a", "b", "c"])
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        assert selector.get_value() == ""

    def test_select_all_with_no_checkboxes(self, selector):
        """Toggling Select All with no tests loaded does not raise."""
        selector.set_tests([])
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        assert selector.get_value() == "all"  # vacuously all

    def test_partial_state_does_not_check_items(self, selector):
        """Setting Select All to PartiallyChecked does not modify individual checkboxes.

        The _on_select_all handler only acts on Checked state; PartiallyChecked
        leaves items unchanged.
        """
        selector.set_tests(["a", "b", "c"])
        # Uncheck one so we have a known state
        selector._checkboxes[1][1].setChecked(False)
        checked_before = [cb.isChecked() for _, cb in selector._checkboxes]
        selector._select_all.setCheckState(Qt.CheckState.PartiallyChecked)
        checked_after = [cb.isChecked() for _, cb in selector._checkboxes]
        assert checked_before == checked_after


# ---------------------------------------------------------------------------
# _on_item_changed: tri-state logic
# ---------------------------------------------------------------------------


class TestTriState:
    """Tests for tri-state Select All driven by individual checkbox changes."""

    def test_all_checked_sets_select_all_checked(self, selector):
        """When all items are checked, Select All transitions to Checked."""
        selector.set_tests(["a", "b", "c"])
        # All start checked, so Select All should be Checked
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_none_checked_sets_select_all_unchecked(self, selector):
        """When no items are checked, Select All transitions to Unchecked."""
        selector.set_tests(["a", "b", "c"])
        for _, cb in selector._checkboxes:
            cb.setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked

    def test_some_checked_sets_select_all_partial(self, selector):
        """Checking some (not all) items sets Select All to PartiallyChecked."""
        selector.set_tests(["a", "b", "c"])
        selector._checkboxes[0][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked

    def test_uncheck_one_from_all_sets_partial(self, selector):
        """Unchecking one item from a fully checked set triggers PartiallyChecked."""
        selector.set_tests(["a", "b", "c"])
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        selector._checkboxes[1][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked

    def test_recheck_last_item_transitions_to_checked(self, selector):
        """Checking the final unchecked item transitions Select All to Checked."""
        selector.set_tests(["a", "b"])
        selector._checkboxes[0][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.PartiallyChecked
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_uncheck_all_one_by_one_transitions_to_unchecked(self, selector):
        """Unchecking all items one at a time transitions to Unchecked."""
        selector.set_tests(["a", "b", "c"])
        for _, cb in selector._checkboxes:
            cb.setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked

    def test_rapid_toggle_maintains_consistency(self, selector):
        """Rapid check/uncheck cycles keep tri-state consistent."""
        selector.set_tests(["a", "b", "c"])
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
        # Check all one by one
        for _, cb in selector._checkboxes:
            cb.setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked

    def test_single_item_toggles_between_checked_and_unchecked(self, selector):
        """With a single test, Select All is either Checked or Unchecked (never partial)."""
        selector.set_tests(["only"])
        assert selector._select_all.checkState() == Qt.CheckState.Checked
        selector._checkboxes[0][1].setChecked(False)
        assert selector._select_all.checkState() == Qt.CheckState.Unchecked
        selector._checkboxes[0][1].setChecked(True)
        assert selector._select_all.checkState() == Qt.CheckState.Checked


# ---------------------------------------------------------------------------
# selection_changed signal emission
# ---------------------------------------------------------------------------


class TestSelectionChangedSignal:
    """Tests for selection_changed signal emission."""

    def test_signal_emitted_on_item_uncheck(self, selector):
        """Unchecking an individual item emits selection_changed."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[0][1].setChecked(False)
        assert len(results) == 1

    def test_signal_emitted_on_item_check(self, selector):
        """Checking an individual item emits selection_changed."""
        results = []
        selector.set_tests(["a", "b"])
        selector._checkboxes[0][1].setChecked(False)  # Uncheck first
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[0][1].setChecked(True)
        assert len(results) == 1

    def test_signal_payload_is_all_when_all_checked(self, selector):
        """Signal carries 'all' when all checkboxes are checked."""
        results = []
        selector.set_tests(["a", "b"])
        selector._checkboxes[0][1].setChecked(False)
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[0][1].setChecked(True)
        assert results[-1] == "all"

    def test_signal_payload_is_comma_separated_for_subset(self, selector):
        """Signal carries comma-separated names when a subset is checked."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[1][1].setChecked(False)
        assert results[-1] == "a, c"

    def test_signal_emitted_on_select_all_check(self, selector):
        """Toggling Select All to Checked emits selection_changed."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._select_all.setCheckState(Qt.CheckState.Checked)
        assert len(results) == 1
        assert results[0] == "all"

    def test_signal_emitted_on_select_all_uncheck(self, selector):
        """Toggling Select All to Unchecked emits selection_changed."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._select_all.setCheckState(Qt.CheckState.Unchecked)
        assert len(results) == 1
        assert results[0] == ""

    def test_no_signal_during_set_tests(self, selector):
        """set_tests() does not emit selection_changed (suppress flag active)."""
        results = []
        selector.selection_changed.connect(lambda v: results.append(v))
        selector.set_tests(["a", "b", "c"])
        assert len(results) == 0

    def test_multiple_changes_emit_multiple_signals(self, selector):
        """Each individual checkbox change emits a separate signal."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[0][1].setChecked(False)
        selector._checkboxes[1][1].setChecked(False)
        selector._checkboxes[2][1].setChecked(False)
        assert len(results) == 3

    def test_signal_payload_reflects_current_state(self, selector):
        """Each emitted value reflects the current selection state at emission time."""
        results = []
        selector.set_tests(["a", "b", "c"])
        selector.selection_changed.connect(lambda v: results.append(v))
        selector._checkboxes[0][1].setChecked(False)
        selector._checkboxes[1][1].setChecked(False)
        # After first uncheck: b, c remain
        assert results[0] == "b, c"
        # After second uncheck: only c remains
        assert results[1] == "c"


# ---------------------------------------------------------------------------
# _update_scroll_height: scroll area sizing
# ---------------------------------------------------------------------------


class TestScrollHeight:
    """Tests for scroll area height calculation."""

    def test_small_list_uses_exact_height(self, selector):
        """Few items produce height = n * _ROW_HEIGHT + _PADDING."""
        selector.set_tests(["a", "b"])
        expected = 2 * _ROW_HEIGHT + _PADDING
        assert selector._scroll.minimumHeight() == expected
        assert selector._scroll.maximumHeight() == expected

    def test_large_list_capped_at_max_height(self, selector):
        """Many items cap the scroll area at _MAX_HEIGHT."""
        # Create enough tests to exceed _MAX_HEIGHT
        many_tests = [f"test_{i}" for i in range(50)]
        selector.set_tests(many_tests)
        assert selector._scroll.minimumHeight() == _MAX_HEIGHT
        assert selector._scroll.maximumHeight() == _MAX_HEIGHT

    def test_empty_list_has_padding_height(self, selector):
        """With zero tests, height is just _PADDING (0 * _ROW_HEIGHT + _PADDING)."""
        selector.set_tests([])
        expected = _PADDING
        assert selector._scroll.minimumHeight() == expected
        assert selector._scroll.maximumHeight() == expected

    def test_height_updates_on_rebuild(self, selector):
        """Rebuilding with a different number of tests updates the scroll height."""
        selector.set_tests(["a", "b", "c"])
        h1 = selector._scroll.minimumHeight()
        selector.set_tests(["x"])
        h2 = selector._scroll.minimumHeight()
        assert h1 != h2
        assert h2 == 1 * _ROW_HEIGHT + _PADDING
