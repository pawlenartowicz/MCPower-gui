"""Tests for ResultsTab — closeable subtabs for each analysis run."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QWidget

from mcpower_gui.tabs.results_tab import ResultsTab

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def tab():
    """ResultsTab with ResultPanel mocked to return a lightweight QWidget."""
    with patch("mcpower_gui.tabs.results_tab.ResultPanel") as mock_cls:
        mock_cls.side_effect = lambda *a, **kw: QWidget()
        widget = ResultsTab()
        yield widget
        widget.deleteLater()


def _add_power_result(tab, formula="y = x1 + x2", sample_size=100, record_id=None):
    """Helper to add a power-mode result with sensible defaults."""
    return tab.add_result(
        mode="power",
        result={},
        target_power=0.8,
        script="",
        analysis_params={"_formula": formula, "sample_size": sample_size},
        model_type="linear_regression",
        record_id=record_id,
    )


def _add_ss_result(tab, formula="y = x1 + x2", ss_from=30, ss_to=200, record_id=None):
    """Helper to add a sample-size-mode result with sensible defaults."""
    return tab.add_result(
        mode="sample_size",
        result={},
        target_power=0.8,
        script="",
        analysis_params={"_formula": formula, "ss_from": ss_from, "ss_to": ss_to},
        model_type="linear_regression",
        record_id=record_id,
    )


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestInitialState:
    """Tests for ResultsTab initial state on construction."""

    def test_placeholder_shown_initially(self, tab):
        """Placeholder is the visible widget when no results have been added."""
        assert tab._stack.currentWidget() is tab._placeholder

    def test_tab_widget_has_no_tabs(self, tab):
        """Tab widget starts with zero tabs."""
        assert tab._tab_widget.count() == 0

    def test_tracking_dicts_empty(self, tab):
        """All tracking dictionaries are empty at construction."""
        assert len(tab._tab_times) == 0
        assert len(tab._tab_base_names) == 0
        assert len(tab._tab_record_ids) == 0

    def test_name_timer_not_active(self, tab):
        """The name-update timer is not running initially."""
        assert not tab._name_timer.isActive()


# ---------------------------------------------------------------------------
# add_result: tab name construction
# ---------------------------------------------------------------------------


class TestAddResultTabName:
    """Tests for tab name construction in add_result()."""

    def test_power_mode_tab_name_format(self, tab):
        """Power mode tab name follows 'formula | Power N=ss | HH:MM' format."""
        _add_power_result(tab, formula="y = x1 + x2", sample_size=100)
        name = tab._tab_widget.tabText(0)
        assert "y = x1 + x2" in name
        assert "Power N=100" in name
        # Contains a time portion HH:MM
        assert " | " in name

    def test_sample_size_mode_tab_name_format(self, tab):
        """Sample size mode tab name follows 'formula | SS from->to | HH:MM' format."""
        _add_ss_result(tab, formula="y = x1", ss_from=30, ss_to=200)
        name = tab._tab_widget.tabText(0)
        assert "y = x1" in name
        assert "SS 30\u2192200" in name

    def test_anova_prefix(self, tab):
        """ANOVA model type uses 'ANOVA' prefix regardless of formula."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params={"_formula": "y = group * treatment", "sample_size": 50},
            model_type="anova",
        )
        name = tab._tab_widget.tabText(0)
        assert name.startswith("ANOVA")
        assert "Power N=50" in name

    def test_no_formula_uses_lm_prefix(self, tab):
        """When no formula is provided, prefix defaults to 'lm'."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params={"sample_size": 100},
            model_type="linear_regression",
        )
        name = tab._tab_widget.tabText(0)
        assert name.startswith("lm")

    def test_empty_formula_uses_lm_prefix(self, tab):
        """When formula is empty string, prefix defaults to 'lm'."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params={"_formula": "", "sample_size": 100},
            model_type="linear_regression",
        )
        name = tab._tab_widget.tabText(0)
        assert name.startswith("lm")

    def test_none_analysis_params_uses_lm_prefix(self, tab):
        """When analysis_params is None, prefix defaults to 'lm'."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params=None,
            model_type="linear_regression",
        )
        name = tab._tab_widget.tabText(0)
        assert name.startswith("lm")

    def test_none_analysis_params_power_mode_shows_question_mark(self, tab):
        """When analysis_params is None in power mode, sample size shows '?'."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params=None,
        )
        name = tab._tab_widget.tabText(0)
        assert "Power N=?" in name

    def test_none_analysis_params_ss_mode_shows_question_marks(self, tab):
        """When analysis_params is None in ss mode, from/to show '?'."""
        tab.add_result(
            mode="sample_size",
            result={},
            target_power=0.8,
            script="",
            analysis_params=None,
        )
        name = tab._tab_widget.tabText(0)
        assert "SS ?\u2192?" in name

    def test_tab_name_contains_time(self, tab):
        """Tab name contains current time in HH:MM format."""
        now = datetime.now()
        _add_power_result(tab)
        name = tab._tab_widget.tabText(0)
        expected_time = now.strftime("%H:%M")
        assert expected_time in name


# ---------------------------------------------------------------------------
# add_result: formula truncation
# ---------------------------------------------------------------------------


class TestAddResultFormulaTruncation:
    """Tests for formula truncation when formula exceeds 30 characters."""

    def test_short_formula_not_truncated(self, tab):
        """Formula with <= 30 chars is not truncated."""
        short_formula = "y = x1 + x2"  # 11 chars
        _add_power_result(tab, formula=short_formula)
        name = tab._tab_widget.tabText(0)
        assert short_formula in name
        assert "..." not in name

    def test_exactly_30_chars_not_truncated(self, tab):
        """Formula with exactly 30 chars is not truncated."""
        formula_30 = "a" * 30
        _add_power_result(tab, formula=formula_30)
        name = tab._tab_widget.tabText(0)
        assert formula_30 in name
        assert "..." not in name

    def test_31_chars_truncated(self, tab):
        """Formula with 31 chars is truncated to 27 chars + '...'."""
        formula_31 = "a" * 31
        _add_power_result(tab, formula=formula_31)
        name = tab._tab_widget.tabText(0)
        expected_prefix = "a" * 27 + "..."
        assert expected_prefix in name
        assert formula_31 not in name

    def test_long_formula_truncated(self, tab):
        """Long formula (>30 chars) is truncated to first 27 chars + '...'."""
        long_formula = "y = x1 + x2 + x3 + x4 + x5 + x6 + x7"
        assert len(long_formula) > 30
        _add_power_result(tab, formula=long_formula)
        name = tab._tab_widget.tabText(0)
        expected_prefix = long_formula[:27] + "..."
        assert expected_prefix in name
        assert long_formula not in name

    def test_truncated_prefix_length(self, tab):
        """Truncated prefix is always exactly 30 chars (27 + 3 for '...')."""
        long_formula = "y = x1 + x2 + x3 + x4 + x5 + x6 + x7"
        _add_power_result(tab, formula=long_formula)
        name = tab._tab_widget.tabText(0)
        # The prefix part is before the first " | "
        prefix = name.split(" | ")[0]
        assert len(prefix) == 30


# ---------------------------------------------------------------------------
# add_result: tracking dicts populated
# ---------------------------------------------------------------------------


class TestAddResultTrackingDicts:
    """Tests for tracking dictionaries populated by add_result()."""

    def test_tab_times_populated(self, tab):
        """add_result populates _tab_times with creation datetime."""
        panel = _add_power_result(tab)
        assert id(panel) in tab._tab_times
        assert isinstance(tab._tab_times[id(panel)], datetime)

    def test_tab_base_names_populated(self, tab):
        """add_result populates _tab_base_names with the constructed tab name."""
        panel = _add_power_result(tab, formula="y = x1")
        assert id(panel) in tab._tab_base_names
        assert "y = x1" in tab._tab_base_names[id(panel)]

    def test_tab_record_ids_populated_when_provided(self, tab):
        """add_result populates _tab_record_ids when record_id is given."""
        panel = _add_power_result(tab, record_id="rec-123")
        assert id(panel) in tab._tab_record_ids
        assert tab._tab_record_ids[id(panel)] == "rec-123"

    def test_tab_record_ids_not_populated_when_none(self, tab):
        """add_result does not populate _tab_record_ids when record_id is None."""
        panel = _add_power_result(tab, record_id=None)
        assert id(panel) not in tab._tab_record_ids

    def test_multiple_results_tracked_independently(self, tab):
        """Multiple add_result calls create independent tracking entries."""
        p1 = _add_power_result(tab, formula="a = b", record_id="r1")
        p2 = _add_ss_result(tab, formula="c = d", record_id="r2")
        assert id(p1) in tab._tab_times
        assert id(p2) in tab._tab_times
        assert id(p1) in tab._tab_base_names
        assert id(p2) in tab._tab_base_names
        assert tab._tab_record_ids[id(p1)] == "r1"
        assert tab._tab_record_ids[id(p2)] == "r2"


# ---------------------------------------------------------------------------
# add_result: stack and timer behavior
# ---------------------------------------------------------------------------


class TestAddResultStackAndTimer:
    """Tests for stack widget switching and timer start on add_result()."""

    def test_switches_to_tab_widget(self, tab):
        """After add_result, the stack shows the tab widget (not placeholder)."""
        _add_power_result(tab)
        assert tab._stack.currentWidget() is tab._tab_widget

    def test_selects_new_tab(self, tab):
        """add_result selects the newly created tab."""
        _add_power_result(tab, formula="first")
        _add_power_result(tab, formula="second")
        assert tab._tab_widget.currentIndex() == 1

    def test_timer_started_after_first_add(self, tab):
        """The name timer starts after the first add_result call."""
        assert not tab._name_timer.isActive()
        _add_power_result(tab)
        assert tab._name_timer.isActive()

    def test_tab_count_increments(self, tab):
        """Each add_result increments the tab count."""
        assert tab._tab_widget.count() == 0
        _add_power_result(tab)
        assert tab._tab_widget.count() == 1
        _add_power_result(tab)
        assert tab._tab_widget.count() == 2
        _add_ss_result(tab)
        assert tab._tab_widget.count() == 3


# ---------------------------------------------------------------------------
# _close_tab: tracking cleanup
# ---------------------------------------------------------------------------


class TestCloseTab:
    """Tests for _close_tab() tracking cleanup and placeholder behavior."""

    def test_close_removes_tab(self, tab):
        """Closing a tab removes it from the tab widget."""
        _add_power_result(tab)
        assert tab._tab_widget.count() == 1
        tab._close_tab(0)
        assert tab._tab_widget.count() == 0

    def test_close_cleans_tab_times(self, tab):
        """Closing a tab removes its entry from _tab_times."""
        panel = _add_power_result(tab)
        panel_id = id(panel)
        tab._close_tab(0)
        assert panel_id not in tab._tab_times

    def test_close_cleans_tab_base_names(self, tab):
        """Closing a tab removes its entry from _tab_base_names."""
        panel = _add_power_result(tab)
        panel_id = id(panel)
        tab._close_tab(0)
        assert panel_id not in tab._tab_base_names

    def test_close_cleans_tab_record_ids(self, tab):
        """Closing a tab removes its entry from _tab_record_ids."""
        panel = _add_power_result(tab, record_id="rec-abc")
        panel_id = id(panel)
        tab._close_tab(0)
        assert panel_id not in tab._tab_record_ids

    def test_close_without_record_id_no_error(self, tab):
        """Closing a tab without a record_id does not raise an error."""
        _add_power_result(tab, record_id=None)
        tab._close_tab(0)  # Should not raise

    def test_placeholder_shown_when_last_tab_closed(self, tab):
        """Placeholder is shown when the last tab is closed."""
        _add_power_result(tab)
        assert tab._stack.currentWidget() is tab._tab_widget
        tab._close_tab(0)
        assert tab._stack.currentWidget() is tab._placeholder

    def test_timer_stopped_when_last_tab_closed(self, tab):
        """Name timer is stopped when the last tab is closed."""
        _add_power_result(tab)
        assert tab._name_timer.isActive()
        tab._close_tab(0)
        assert not tab._name_timer.isActive()

    def test_placeholder_not_shown_when_tabs_remain(self, tab):
        """Placeholder is not shown when other tabs remain after closing one."""
        _add_power_result(tab, formula="first")
        _add_power_result(tab, formula="second")
        tab._close_tab(0)
        assert tab._tab_widget.count() == 1
        assert tab._stack.currentWidget() is tab._tab_widget

    def test_timer_still_active_when_tabs_remain(self, tab):
        """Timer continues running when other tabs remain after closing one."""
        _add_power_result(tab)
        _add_power_result(tab)
        tab._close_tab(0)
        assert tab._name_timer.isActive()

    def test_close_middle_tab_preserves_others(self, tab):
        """Closing a middle tab does not disturb other tabs' tracking."""
        p1 = _add_power_result(tab, formula="first", record_id="r1")
        p2 = _add_power_result(tab, formula="second", record_id="r2")
        p3 = _add_power_result(tab, formula="third", record_id="r3")
        # Close middle tab (index 1)
        tab._close_tab(1)
        assert tab._tab_widget.count() == 2
        # p1 and p3 should still be tracked
        assert id(p1) in tab._tab_times
        assert id(p3) in tab._tab_times
        assert id(p2) not in tab._tab_times


# ---------------------------------------------------------------------------
# _close_others: multi-tab removal
# ---------------------------------------------------------------------------


class TestCloseOthers:
    """Tests for _close_others() multi-tab removal."""

    def test_close_others_keeps_only_specified(self, tab):
        """_close_others keeps only the tab at keep_index."""
        _add_power_result(tab, formula="first")
        _add_power_result(tab, formula="second")
        _add_power_result(tab, formula="third")
        assert tab._tab_widget.count() == 3
        tab._close_others(1)
        assert tab._tab_widget.count() == 1

    def test_close_others_keeps_correct_tab(self, tab):
        """_close_others keeps the correct tab based on its base name."""
        _add_power_result(tab, formula="first")
        p2 = _add_power_result(tab, formula="second")
        _add_power_result(tab, formula="third")
        tab._close_others(1)
        # The remaining tab's widget should be p2
        remaining = tab._tab_widget.widget(0)
        assert remaining is p2

    def test_close_others_cleans_tracking(self, tab):
        """_close_others cleans tracking dicts for removed tabs."""
        p1 = _add_power_result(tab, formula="first", record_id="r1")
        p2 = _add_power_result(tab, formula="second", record_id="r2")
        p3 = _add_power_result(tab, formula="third", record_id="r3")
        tab._close_others(1)
        assert id(p1) not in tab._tab_times
        assert id(p3) not in tab._tab_times
        assert id(p2) in tab._tab_times

    def test_close_others_with_single_tab(self, tab):
        """_close_others with a single tab keeps that tab."""
        _add_power_result(tab)
        tab._close_others(0)
        assert tab._tab_widget.count() == 1

    def test_close_others_timer_still_active(self, tab):
        """Timer remains active when one tab is kept."""
        _add_power_result(tab)
        _add_power_result(tab)
        tab._close_others(0)
        assert tab._name_timer.isActive()

    def test_close_others_keeps_first(self, tab):
        """_close_others(0) keeps the first tab and removes the rest."""
        p1 = _add_power_result(tab, formula="first")
        _add_power_result(tab, formula="second")
        _add_power_result(tab, formula="third")
        tab._close_others(0)
        assert tab._tab_widget.count() == 1
        assert tab._tab_widget.widget(0) is p1

    def test_close_others_keeps_last(self, tab):
        """_close_others(last_index) keeps the last tab."""
        _add_power_result(tab, formula="first")
        _add_power_result(tab, formula="second")
        p3 = _add_power_result(tab, formula="third")
        tab._close_others(2)
        assert tab._tab_widget.count() == 1
        assert tab._tab_widget.widget(0) is p3


# ---------------------------------------------------------------------------
# _close_all: full removal
# ---------------------------------------------------------------------------


class TestCloseAll:
    """Tests for _close_all() complete tab removal."""

    def test_close_all_removes_all_tabs(self, tab):
        """_close_all removes all tabs."""
        _add_power_result(tab)
        _add_power_result(tab)
        _add_power_result(tab)
        assert tab._tab_widget.count() == 3
        tab._close_all()
        assert tab._tab_widget.count() == 0

    def test_close_all_shows_placeholder(self, tab):
        """_close_all shows the placeholder."""
        _add_power_result(tab)
        tab._close_all()
        assert tab._stack.currentWidget() is tab._placeholder

    def test_close_all_stops_timer(self, tab):
        """_close_all stops the name timer."""
        _add_power_result(tab)
        assert tab._name_timer.isActive()
        tab._close_all()
        assert not tab._name_timer.isActive()

    def test_close_all_cleans_all_tracking(self, tab):
        """_close_all cleans all tracking dictionaries."""
        _add_power_result(tab, record_id="r1")
        _add_power_result(tab, record_id="r2")
        tab._close_all()
        assert len(tab._tab_times) == 0
        assert len(tab._tab_base_names) == 0
        assert len(tab._tab_record_ids) == 0

    def test_close_all_on_empty_no_error(self, tab):
        """_close_all on an already-empty tab widget does not raise."""
        tab._close_all()  # Should not raise
        assert tab._tab_widget.count() == 0

    def test_close_all_then_add_restores_state(self, tab):
        """After _close_all, adding a new result restores normal state."""
        _add_power_result(tab)
        tab._close_all()
        assert tab._stack.currentWidget() is tab._placeholder
        _add_power_result(tab)
        assert tab._stack.currentWidget() is tab._tab_widget
        assert tab._tab_widget.count() == 1
        assert tab._name_timer.isActive()


# ---------------------------------------------------------------------------
# _update_tab_names: elapsed time formatting
# ---------------------------------------------------------------------------


class TestUpdateTabNames:
    """Tests for _update_tab_names() elapsed time formatting."""

    def test_less_than_60s_no_suffix(self, tab):
        """Tabs less than 60 seconds old show just the base name (no suffix)."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        # Set creation time to 30 seconds ago
        tab._tab_times[id(panel)] = datetime.now() - timedelta(seconds=30)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == base_name

    def test_exactly_60s_shows_1m_ago(self, tab):
        """Tab exactly 60 seconds old shows '(1m ago)' suffix."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(seconds=60)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (1m ago)"

    def test_5_minutes_shows_5m_ago(self, tab):
        """Tab 5 minutes old shows '(5m ago)' suffix."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(minutes=5)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (5m ago)"

    def test_59_minutes_shows_59m_ago(self, tab):
        """Tab 59 minutes old shows '(59m ago)' suffix."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(minutes=59)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (59m ago)"

    def test_exactly_1h_shows_1h_ago(self, tab):
        """Tab exactly 1 hour old shows '(1h ago)' suffix."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(hours=1)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (1h ago)"

    def test_3_hours_shows_3h_ago(self, tab):
        """Tab 3 hours old shows '(3h ago)' suffix."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(hours=3)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (3h ago)"

    def test_90_minutes_shows_1h_ago(self, tab):
        """Tab 90 minutes old shows '(1h ago)' since 90m / 60 = 1.5, int = 1."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(minutes=90)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == f"{base_name} (1h ago)"

    def test_just_under_60s_no_suffix(self, tab):
        """Tab at 59 seconds shows no suffix (still under 60s threshold)."""
        panel = _add_power_result(tab, formula="test")
        base_name = tab._tab_base_names[id(panel)]
        tab._tab_times[id(panel)] = datetime.now() - timedelta(seconds=59)
        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == base_name

    def test_multiple_tabs_different_ages(self, tab):
        """Multiple tabs with different ages each get their correct suffix."""
        p1 = _add_power_result(tab, formula="recent")
        p2 = _add_power_result(tab, formula="older")
        p3 = _add_power_result(tab, formula="oldest")

        base1 = tab._tab_base_names[id(p1)]
        base2 = tab._tab_base_names[id(p2)]
        base3 = tab._tab_base_names[id(p3)]

        tab._tab_times[id(p1)] = datetime.now() - timedelta(seconds=30)
        tab._tab_times[id(p2)] = datetime.now() - timedelta(minutes=10)
        tab._tab_times[id(p3)] = datetime.now() - timedelta(hours=2)

        tab._update_tab_names()
        assert tab._tab_widget.tabText(0) == base1  # no suffix
        assert tab._tab_widget.tabText(1) == f"{base2} (10m ago)"
        assert tab._tab_widget.tabText(2) == f"{base3} (2h ago)"

    def test_update_on_empty_tab_widget_no_error(self, tab):
        """Calling _update_tab_names on empty tab widget does not raise."""
        tab._update_tab_names()  # Should not raise

    def test_missing_tab_times_entry_skipped(self, tab):
        """If a widget has no entry in _tab_times, it is skipped gracefully."""
        panel = _add_power_result(tab, formula="test")
        original_name = tab._tab_widget.tabText(0)
        # Remove the time entry manually to simulate missing data
        del tab._tab_times[id(panel)]
        tab._update_tab_names()
        # Tab text should remain unchanged
        assert tab._tab_widget.tabText(0) == original_name

    def test_missing_base_names_entry_skipped(self, tab):
        """If a widget has no entry in _tab_base_names, it is skipped gracefully."""
        panel = _add_power_result(tab, formula="test")
        original_name = tab._tab_widget.tabText(0)
        # Remove the base name entry manually to simulate missing data
        del tab._tab_base_names[id(panel)]
        tab._update_tab_names()
        # Tab text should remain unchanged
        assert tab._tab_widget.tabText(0) == original_name


# ---------------------------------------------------------------------------
# add_result: mode suffixes
# ---------------------------------------------------------------------------


class TestAddResultModeSuffix:
    """Tests for mode suffix construction in add_result()."""

    def test_power_mode_suffix_with_sample_size(self, tab):
        """Power mode constructs 'Power N=<ss>' suffix."""
        _add_power_result(tab, sample_size=250)
        name = tab._tab_widget.tabText(0)
        assert "Power N=250" in name

    def test_sample_size_mode_suffix_with_range(self, tab):
        """Sample size mode constructs 'SS <from>-><to>' suffix."""
        _add_ss_result(tab, ss_from=50, ss_to=500)
        name = tab._tab_widget.tabText(0)
        assert "SS 50\u2192500" in name

    def test_power_mode_missing_sample_size_shows_question_mark(self, tab):
        """Power mode without sample_size in params shows 'Power N=?'."""
        tab.add_result(
            mode="power",
            result={},
            target_power=0.8,
            script="",
            analysis_params={"_formula": "y = x"},
        )
        name = tab._tab_widget.tabText(0)
        assert "Power N=?" in name

    def test_ss_mode_missing_range_shows_question_marks(self, tab):
        """Sample size mode without ss_from/ss_to shows 'SS ?->?'."""
        tab.add_result(
            mode="sample_size",
            result={},
            target_power=0.8,
            script="",
            analysis_params={"_formula": "y = x"},
        )
        name = tab._tab_widget.tabText(0)
        assert "SS ?\u2192?" in name


# ---------------------------------------------------------------------------
# add_result: returns the panel widget
# ---------------------------------------------------------------------------


class TestAddResultReturnValue:
    """Tests for add_result() return value."""

    def test_returns_widget(self, tab):
        """add_result returns the created panel widget."""
        panel = _add_power_result(tab)
        assert isinstance(panel, QWidget)

    def test_returned_widget_is_in_tab(self, tab):
        """The returned widget is the one placed in the tab."""
        panel = _add_power_result(tab)
        assert tab._tab_widget.widget(0) is panel
