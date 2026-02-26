"""Tests for CorrelationEditor widget."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from mcpower_gui.widgets.correlation_editor import CorrelationEditor, _corr_key

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def editor():
    widget = CorrelationEditor()
    yield widget
    widget.deleteLater()


# ---------------------------------------------------------------------------
# _corr_key standalone function
# ---------------------------------------------------------------------------


class TestCorrKey:
    """Tests for the _corr_key canonical sorting helper."""

    def test_already_sorted(self):
        assert _corr_key("a", "b") == "a,b"

    def test_reverse_order(self):
        """Reversed arguments produce the same canonical key."""
        assert _corr_key("b", "a") == "a,b"

    def test_symmetry(self):
        """_corr_key(x, y) == _corr_key(y, x) for any pair."""
        assert _corr_key("x1", "x2") == _corr_key("x2", "x1")

    def test_identical_vars(self):
        """Same variable passed twice produces 'a,a'."""
        assert _corr_key("a", "a") == "a,a"

    def test_multichar_names(self):
        assert _corr_key("motivation", "age") == "age,motivation"

    def test_numeric_prefix_sorting(self):
        """Lexicographic sort: '1' < 'a'."""
        assert _corr_key("x2", "x1") == "x1,x2"


# ---------------------------------------------------------------------------
# set_variables: grid structure
# ---------------------------------------------------------------------------


class TestSetVariablesGrid:
    """Tests for grid layout after set_variables()."""

    def test_two_vars_creates_one_cell(self, editor):
        """2 variables => 1 lower-triangle cell."""
        editor.set_variables(["a", "b"])
        assert len(editor._cells) == 1
        assert "a,b" in editor._cells

    def test_three_vars_creates_three_cells(self, editor):
        """3 variables => 3 lower-triangle cells (n*(n-1)/2)."""
        editor.set_variables(["a", "b", "c"])
        assert len(editor._cells) == 3
        expected_keys = {"a,b", "a,c", "b,c"}
        assert set(editor._cells.keys()) == expected_keys

    def test_four_vars_creates_six_cells(self, editor):
        """4 variables => 6 lower-triangle cells."""
        editor.set_variables(["a", "b", "c", "d"])
        assert len(editor._cells) == 6
        expected_keys = {"a,b", "a,c", "a,d", "b,c", "b,d", "c,d"}
        assert set(editor._cells.keys()) == expected_keys

    def test_zero_vars_shows_placeholder(self, editor):
        """0 variables shows placeholder label, no cells."""
        editor.set_variables([])
        assert len(editor._cells) == 0
        assert editor._grid.count() == 1  # just the placeholder

    def test_one_var_shows_placeholder(self, editor):
        """1 variable shows placeholder label, no cells."""
        editor.set_variables(["only_one"])
        assert len(editor._cells) == 0
        assert editor._grid.count() == 1

    def test_rebuild_clears_old_cells(self, editor):
        """Calling set_variables again replaces old cells."""
        editor.set_variables(["a", "b", "c"])
        assert len(editor._cells) == 3
        editor.set_variables(["x", "y"])
        assert len(editor._cells) == 1
        assert "x,y" in editor._cells
        assert "a,b" not in editor._cells

    def test_default_cell_value_is_zero(self, editor):
        """Newly created cells default to 0.0."""
        editor.set_variables(["a", "b"])
        assert editor._cells["a,b"].value() == 0.0

    def test_cell_range(self, editor):
        """Cells are bounded to [-0.99, 0.99]."""
        editor.set_variables(["a", "b"])
        spin = editor._cells["a,b"]
        assert spin.minimum() == -0.99
        assert spin.maximum() == 0.99


# ---------------------------------------------------------------------------
# Value preservation across rebuilds
# ---------------------------------------------------------------------------


class TestValuePreservation:
    """Tests that non-zero values survive set_variables rebuilds."""

    def test_value_preserved_same_vars(self, editor):
        """Rebuilding with same variables preserves set values."""
        editor.set_variables(["a", "b", "c"])
        editor._cells["a,b"].setValue(0.5)
        editor._cells["a,c"].setValue(-0.3)

        editor.set_variables(["a", "b", "c"])
        assert editor._cells["a,b"].value() == pytest.approx(0.5)
        assert editor._cells["a,c"].value() == pytest.approx(-0.3)

    def test_value_preserved_superset_vars(self, editor):
        """Adding a new variable preserves existing pair values."""
        editor.set_variables(["a", "b"])
        editor._cells["a,b"].setValue(0.7)

        editor.set_variables(["a", "b", "c"])
        assert editor._cells["a,b"].value() == pytest.approx(0.7)
        # New pairs default to 0.0
        assert editor._cells["a,c"].value() == 0.0
        assert editor._cells["b,c"].value() == 0.0

    def test_value_lost_when_var_removed(self, editor):
        """Removing a variable drops its pair values (no stale keys)."""
        editor.set_variables(["a", "b", "c"])
        editor._cells["a,c"].setValue(0.4)

        # Remove 'c' from variables
        editor.set_variables(["a", "b"])
        assert "a,c" not in editor._cells
        assert len(editor._cells) == 1

    def test_zero_values_not_preserved_via_get(self, editor):
        """get_correlations filters zeros, but set_variables restores zeros from old_values."""
        editor.set_variables(["a", "b", "c"])
        editor._cells["a,b"].setValue(0.0)
        editor._cells["a,c"].setValue(0.5)

        # get_correlations only returns non-zero
        old = editor.get_correlations()
        assert "a,b" not in old
        assert "a,c" in old

        # Rebuild: a,b resets to 0.0 (since it wasn't in old_values), a,c preserved
        editor.set_variables(["a", "b", "c"])
        assert editor._cells["a,b"].value() == 0.0
        assert editor._cells["a,c"].value() == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# set_correlations / get_correlations round-trip
# ---------------------------------------------------------------------------


class TestCorrelationsRoundTrip:
    """Tests for set_correlations() and get_correlations()."""

    def test_set_and_get(self, editor):
        """set_correlations populates cells; get_correlations reads them back."""
        editor.set_variables(["a", "b", "c"])
        editor.set_correlations({"a,b": 0.5, "a,c": -0.3, "b,c": 0.1})
        result = editor.get_correlations()
        assert result == pytest.approx({"a,b": 0.5, "a,c": -0.3, "b,c": 0.1})

    def test_get_filters_zeros(self, editor):
        """get_correlations excludes keys with value 0.0."""
        editor.set_variables(["a", "b", "c"])
        editor.set_correlations({"a,b": 0.5, "a,c": 0.0, "b,c": 0.0})
        result = editor.get_correlations()
        assert "a,b" in result
        assert "a,c" not in result
        assert "b,c" not in result

    def test_set_missing_key_defaults_to_zero(self, editor):
        """Keys not in the correlations dict default to 0.0."""
        editor.set_variables(["a", "b", "c"])
        editor._cells["a,b"].setValue(0.8)
        # set_correlations with only one key — others reset to 0.0
        editor.set_correlations({"b,c": 0.2})
        assert editor._cells["a,b"].value() == 0.0
        assert editor._cells["b,c"].value() == pytest.approx(0.2)
        assert editor._cells["a,c"].value() == 0.0

    def test_empty_dict_zeros_all(self, editor):
        """set_correlations({}) resets every cell to 0.0."""
        editor.set_variables(["a", "b"])
        editor._cells["a,b"].setValue(0.5)
        editor.set_correlations({})
        assert editor._cells["a,b"].value() == 0.0

    def test_get_on_empty_editor(self, editor):
        """get_correlations on editor with no variables returns empty dict."""
        assert editor.get_correlations() == {}

    def test_get_all_keys(self, editor):
        """get_all_keys returns all cell keys regardless of value."""
        editor.set_variables(["a", "b", "c"])
        editor.set_correlations({"a,b": 0.5})
        keys = editor.get_all_keys()
        assert set(keys) == {"a,b", "a,c", "b,c"}

    def test_round_trip_boundary_values(self, editor):
        """Boundary values -0.99 and 0.99 survive round-trip."""
        editor.set_variables(["a", "b", "c"])
        editor.set_correlations({"a,b": 0.99, "a,c": -0.99})
        result = editor.get_correlations()
        assert result["a,b"] == pytest.approx(0.99)
        assert result["a,c"] == pytest.approx(-0.99)


# ---------------------------------------------------------------------------
# set_locked_keys
# ---------------------------------------------------------------------------


class TestSetLockedKeys:
    """Tests for set_locked_keys() selective disable."""

    def test_lock_disables_cells(self, editor):
        """Locked keys have their spinboxes disabled."""
        editor.set_variables(["a", "b", "c"])
        editor.set_locked_keys({"a,b"})
        assert not editor._cells["a,b"].isEnabled()
        assert editor._cells["a,c"].isEnabled()
        assert editor._cells["b,c"].isEnabled()

    def test_lock_multiple_keys(self, editor):
        """Multiple keys can be locked simultaneously."""
        editor.set_variables(["a", "b", "c"])
        editor.set_locked_keys({"a,b", "b,c"})
        assert not editor._cells["a,b"].isEnabled()
        assert editor._cells["a,c"].isEnabled()
        assert not editor._cells["b,c"].isEnabled()

    def test_lock_empty_set_enables_all(self, editor):
        """Empty locked set enables all cells."""
        editor.set_variables(["a", "b", "c"])
        editor.set_locked_keys({"a,b"})
        assert not editor._cells["a,b"].isEnabled()
        editor.set_locked_keys(set())
        assert editor._cells["a,b"].isEnabled()
        assert editor._cells["a,c"].isEnabled()
        assert editor._cells["b,c"].isEnabled()

    def test_lock_nonexistent_key_ignored(self, editor):
        """Locking a key not present in cells does not raise."""
        editor.set_variables(["a", "b"])
        editor.set_locked_keys({"x,y"})  # no such key
        assert editor._cells["a,b"].isEnabled()

    def test_set_enabled_disables_all(self, editor):
        """set_enabled(False) disables every cell."""
        editor.set_variables(["a", "b", "c"])
        editor.set_enabled(False)
        for spin in editor._cells.values():
            assert not spin.isEnabled()

    def test_set_enabled_enables_all(self, editor):
        """set_enabled(True) enables every cell."""
        editor.set_variables(["a", "b", "c"])
        editor.set_enabled(False)
        editor.set_enabled(True)
        for spin in editor._cells.values():
            assert spin.isEnabled()


# ---------------------------------------------------------------------------
# correlations_changed signal
# ---------------------------------------------------------------------------


class TestCorrelationsChangedSignal:
    """Tests for correlations_changed signal emission."""

    def test_signal_emitted_on_cell_change(self, editor):
        """Changing a cell value emits correlations_changed."""
        results = []
        editor.set_variables(["a", "b"])
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor._cells["a,b"].setValue(0.5)
        assert len(results) == 1
        assert results[0] == pytest.approx({"a,b": 0.5})

    def test_signal_contains_only_nonzero(self, editor):
        """Emitted dict from signal filters zero-valued cells."""
        results = []
        editor.set_variables(["a", "b", "c"])
        editor._cells["a,b"].setValue(0.3)
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor._cells["a,c"].setValue(0.6)
        assert len(results) == 1
        assert "a,b" in results[0]
        assert "a,c" in results[0]
        # b,c is still 0.0 — should not appear
        assert "b,c" not in results[0]

    def test_signal_not_emitted_by_set_correlations(self, editor):
        """set_correlations blocks signals so no emission occurs."""
        results = []
        editor.set_variables(["a", "b"])
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor.set_correlations({"a,b": 0.5})
        assert len(results) == 0

    def test_multiple_changes_emit_multiple_signals(self, editor):
        """Each cell change emits a separate signal."""
        results = []
        editor.set_variables(["a", "b", "c"])
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor._cells["a,b"].setValue(0.1)
        editor._cells["a,c"].setValue(0.2)
        editor._cells["b,c"].setValue(0.3)
        assert len(results) == 3

    def test_signal_payload_reflects_current_state(self, editor):
        """Each emitted dict reflects the full current state of all non-zero cells."""
        results = []
        editor.set_variables(["a", "b", "c"])
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor._cells["a,b"].setValue(0.1)
        editor._cells["a,c"].setValue(0.2)

        # Second emission should include both a,b and a,c
        assert len(results) == 2
        assert "a,b" in results[1]
        assert "a,c" in results[1]

    def test_setting_to_zero_emits_signal(self, editor):
        """Setting a cell back to 0.0 still emits the signal."""
        results = []
        editor.set_variables(["a", "b"])
        editor._cells["a,b"].setValue(0.5)
        editor.correlations_changed.connect(lambda d: results.append(d))
        editor._cells["a,b"].setValue(0.0)
        assert len(results) == 1
        # Since value is 0.0, get_correlations filters it out
        assert results[0] == {}
