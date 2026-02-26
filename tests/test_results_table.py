"""Tests for ResultsTable widget and ResultPanel CSV export."""

import csv
import io
import os
import tempfile
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from mcpower_gui.widgets.results_table import ResultsTable

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def table():
    widget = ResultsTable()
    yield widget
    widget.deleteLater()


def _cell(table, row, col):
    """Read cell text from the underlying QTableWidget."""
    return table._table.item(row, col).text()


def _header(table, col):
    """Read header text from the underlying QTableWidget."""
    return table._table.horizontalHeaderItem(col).text()


# ---------------------------------------------------------------------------
# show_power_results
# ---------------------------------------------------------------------------


class TestShowPowerResults:
    """Tests for show_power_results()."""

    def test_uncorrected_only_column_count(self, table):
        """Without corrected powers, table should have 3 columns."""
        powers = {"x1": 85.0, "x2": 60.0}
        table.show_power_results(powers, target_power=80.0)
        assert table._table.columnCount() == 3

    def test_uncorrected_only_headers(self, table):
        """Without corrected powers, headers are Variable/Power/Achieved."""
        powers = {"x1": 85.0}
        table.show_power_results(powers, target_power=80.0)
        assert _header(table, 0) == "Tested Variable"
        assert _header(table, 1) == "Power (%)"
        assert _header(table, 2) == "Achieved"

    def test_uncorrected_only_row_count(self, table):
        """Row count matches number of effects."""
        powers = {"x1": 85.0, "x2": 60.0, "x1:x2": 40.0}
        table.show_power_results(powers, target_power=80.0)
        assert table._table.rowCount() == 3

    def test_uncorrected_only_values(self, table):
        """Cell values for uncorrected power results."""
        powers = {"x1": 85.3, "x2": 60.7}
        table.show_power_results(powers, target_power=80.0)
        assert _cell(table, 0, 0) == "x1"
        assert _cell(table, 0, 1) == "85.3"
        assert _cell(table, 1, 0) == "x2"
        assert _cell(table, 1, 1) == "60.7"

    def test_achieved_yes_when_at_target(self, table):
        """Power exactly at target shows 'Yes'."""
        powers = {"x1": 80.0}
        table.show_power_results(powers, target_power=80.0)
        assert _cell(table, 0, 2) == "Yes"

    def test_achieved_yes_when_above_target(self, table):
        """Power above target shows 'Yes'."""
        powers = {"x1": 95.0}
        table.show_power_results(powers, target_power=80.0)
        assert _cell(table, 0, 2) == "Yes"

    def test_achieved_no_when_below_target(self, table):
        """Power below target shows 'No'."""
        powers = {"x1": 79.9}
        table.show_power_results(powers, target_power=80.0)
        assert _cell(table, 0, 2) == "No"

    def test_with_corrected_column_count(self, table):
        """With corrected powers, table should have 5 columns."""
        powers = {"x1": 85.0}
        corrected = {"x1": 75.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        assert table._table.columnCount() == 5

    def test_with_corrected_headers(self, table):
        """With corrected powers, headers include corrected columns."""
        powers = {"x1": 85.0}
        corrected = {"x1": 75.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        assert _header(table, 0) == "Tested Variable"
        assert _header(table, 1) == "Power (%)"
        assert _header(table, 2) == "Achieved"
        assert _header(table, 3) == "Corrected (%)"
        assert _header(table, 4) == "Corrected Achieved"

    def test_with_corrected_values(self, table):
        """Corrected power and achieved values are displayed."""
        powers = {"x1": 90.0}
        corrected = {"x1": 82.5}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        assert _cell(table, 0, 3) == "82.5"
        assert _cell(table, 0, 4) == "Yes"

    def test_corrected_achieved_no(self, table):
        """Corrected power below target shows 'No'."""
        powers = {"x1": 90.0}
        corrected = {"x1": 70.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        assert _cell(table, 0, 4) == "No"

    def test_missing_corrected_shows_dash(self, table):
        """Effect present in uncorrected but missing from corrected shows em-dash."""
        powers = {"x1": 85.0, "x2": 60.0}
        corrected = {"x1": 75.0}  # x2 is missing
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        assert _cell(table, 0, 3) == "75.0"  # x1 has corrected
        assert _cell(table, 1, 3) == "\u2014"  # x2 missing -> em-dash
        assert _cell(table, 1, 4) == "\u2014"

    def test_empty_corrected_dict_treated_as_no_correction(self, table):
        """An empty corrected dict results in 3-column layout (no correction)."""
        powers = {"x1": 85.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected={})
        assert table._table.columnCount() == 3

    def test_none_corrected_treated_as_no_correction(self, table):
        """None corrected dict results in 3-column layout."""
        powers = {"x1": 85.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=None)
        assert table._table.columnCount() == 3

    def test_multiple_effects_order_preserved(self, table):
        """Effects appear in dict insertion order."""
        powers = {"beta": 70.0, "alpha": 90.0, "gamma": 50.0}
        table.show_power_results(powers, target_power=80.0)
        assert _cell(table, 0, 0) == "beta"
        assert _cell(table, 1, 0) == "alpha"
        assert _cell(table, 2, 0) == "gamma"


# ---------------------------------------------------------------------------
# show_sample_size_results
# ---------------------------------------------------------------------------


class TestShowSampleSizeResults:
    """Tests for show_sample_size_results()."""

    def test_uncorrected_column_count(self, table):
        """Without corrected, table should have 3 columns."""
        achieved = {"x1": 100, "x2": 200}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert table._table.columnCount() == 3

    def test_uncorrected_headers(self, table):
        """Headers for uncorrected sample size results."""
        achieved = {"x1": 100}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _header(table, 0) == "Tested Variable"
        assert _header(table, 1) == "Required N"
        assert _header(table, 2) == "Target Power (%)"

    def test_achieved_values(self, table):
        """Achieved sample sizes are displayed as integers."""
        achieved = {"x1": 150, "x2": 300}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _cell(table, 0, 0) == "x1"
        assert _cell(table, 0, 1) == "150"
        assert _cell(table, 1, 1) == "300"

    def test_target_power_displayed(self, table):
        """Target power column shows the correct value."""
        achieved = {"x1": 100}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _cell(table, 0, 2) == "80.0"

    def test_not_achieved_none_without_max_n(self, table):
        """None value without max_n shows 'Not achieved'."""
        achieved = {"x1": None}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _cell(table, 0, 1) == "Not achieved"

    def test_not_achieved_none_with_max_n(self, table):
        """None value with max_n shows '> N' text."""
        achieved = {"x1": None}
        table.show_sample_size_results(achieved, target_power=80.0, max_n=500)
        assert _cell(table, 0, 1) == "> 500"

    def test_negative_value_treated_as_not_achieved(self, table):
        """Negative value (sentinel) treated as not achieved."""
        achieved = {"x1": -1}
        table.show_sample_size_results(achieved, target_power=80.0, max_n=1000)
        assert _cell(table, 0, 1) == "> 1000"

    def test_negative_value_without_max_n(self, table):
        """Negative value without max_n shows 'Not achieved'."""
        achieved = {"x1": -1}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _cell(table, 0, 1) == "Not achieved"

    def test_with_corrected_column_count(self, table):
        """With corrected, table should have 4 columns."""
        achieved = {"x1": 100}
        corrected = {"x1": 120}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected=corrected
        )
        assert table._table.columnCount() == 4

    def test_with_corrected_headers(self, table):
        """With corrected, headers include 'Corrected N'."""
        achieved = {"x1": 100}
        corrected = {"x1": 120}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected=corrected
        )
        assert _header(table, 3) == "Corrected N"

    def test_corrected_values(self, table):
        """Corrected N column shows achieved values."""
        achieved = {"x1": 100}
        corrected = {"x1": 150}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected=corrected
        )
        assert _cell(table, 0, 3) == "150"

    def test_corrected_not_achieved_with_max_n(self, table):
        """Corrected column shows '> N' for not-achieved."""
        achieved = {"x1": 100}
        corrected = {"x1": None}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected=corrected, max_n=500
        )
        assert _cell(table, 0, 3) == "> 500"

    def test_corrected_not_achieved_without_max_n(self, table):
        """Corrected column shows 'Not achieved' when no max_n."""
        achieved = {"x1": 100}
        corrected = {"x1": None}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected=corrected
        )
        assert _cell(table, 0, 3) == "Not achieved"

    def test_empty_corrected_treated_as_no_correction(self, table):
        """An empty corrected dict results in 3-column layout."""
        achieved = {"x1": 100}
        table.show_sample_size_results(
            achieved, target_power=80.0, first_achieved_corrected={}
        )
        assert table._table.columnCount() == 3

    def test_mixed_achieved_and_not(self, table):
        """Mix of achieved and not-achieved effects."""
        achieved = {"x1": 120, "x2": None, "x3": -1}
        table.show_sample_size_results(achieved, target_power=80.0, max_n=500)
        assert _cell(table, 0, 1) == "120"
        assert _cell(table, 1, 1) == "> 500"
        assert _cell(table, 2, 1) == "> 500"

    def test_zero_n_is_valid(self, table):
        """N=0 is a valid achieved value (edge case)."""
        achieved = {"x1": 0}
        table.show_sample_size_results(achieved, target_power=80.0)
        assert _cell(table, 0, 1) == "0"


# ---------------------------------------------------------------------------
# show_scenario_power_results
# ---------------------------------------------------------------------------


class TestShowScenarioPowerResults:
    """Tests for show_scenario_power_results()."""

    def _make_scenario(self, individual_powers):
        """Helper to build a scenario dict with the expected nested structure."""
        return {"results": {"individual_powers": individual_powers}}

    def test_column_count_and_headers(self, table):
        """Scenario power table always has 4 columns."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 95.0}),
            "realistic": self._make_scenario({"x1": 80.0}),
            "doomer": self._make_scenario({"x1": 60.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert table._table.columnCount() == 4
        assert _header(table, 0) == "Tested Variable"
        assert _header(table, 1) == "Optimistic (%)"
        assert _header(table, 2) == "Realistic (%)"
        assert _header(table, 3) == "Doomer (%)"

    def test_all_scenarios_present(self, table):
        """All three scenario columns populated when all present."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 95.0, "x2": 88.0}),
            "realistic": self._make_scenario({"x1": 80.0, "x2": 72.0}),
            "doomer": self._make_scenario({"x1": 60.0, "x2": 45.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert table._table.rowCount() == 2
        # x1 row
        assert _cell(table, 0, 0) == "x1"
        assert _cell(table, 0, 1) == "95.0"
        assert _cell(table, 0, 2) == "80.0"
        assert _cell(table, 0, 3) == "60.0"
        # x2 row
        assert _cell(table, 1, 0) == "x2"
        assert _cell(table, 1, 1) == "88.0"
        assert _cell(table, 1, 2) == "72.0"
        assert _cell(table, 1, 3) == "45.0"

    def test_scenario_order_is_optimistic_realistic_doomer(self, table):
        """Scenarios iterate in SCENARIO_ORDER regardless of dict key order."""
        scenarios = {
            "doomer": self._make_scenario({"x1": 30.0}),
            "optimistic": self._make_scenario({"x1": 90.0}),
            "realistic": self._make_scenario({"x1": 70.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert _cell(table, 0, 1) == "90.0"  # optimistic
        assert _cell(table, 0, 2) == "70.0"  # realistic
        assert _cell(table, 0, 3) == "30.0"  # doomer

    def test_missing_scenario_shows_dash(self, table):
        """Missing scenario results in em-dash for that column."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 95.0}),
            # realistic missing entirely
            "doomer": self._make_scenario({"x1": 60.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert _cell(table, 0, 1) == "95.0"
        assert _cell(table, 0, 2) == "\u2014"  # em-dash for missing realistic
        assert _cell(table, 0, 3) == "60.0"

    def test_missing_effect_in_one_scenario_shows_dash(self, table):
        """Effect present in some scenarios but missing from another shows dash."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 95.0, "x2": 88.0}),
            "realistic": self._make_scenario({"x1": 80.0}),  # x2 missing
            "doomer": self._make_scenario({"x1": 60.0, "x2": 45.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert _cell(table, 1, 2) == "\u2014"  # x2 missing in realistic

    def test_effects_from_first_available_scenario(self, table):
        """Effect list comes from the first scenario found in SCENARIO_ORDER."""
        scenarios = {
            # optimistic missing
            "realistic": self._make_scenario({"a": 70.0, "b": 50.0}),
            "doomer": self._make_scenario({"a": 40.0, "b": 30.0}),
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        assert table._table.rowCount() == 2
        assert _cell(table, 0, 0) == "a"
        assert _cell(table, 1, 0) == "b"
        # optimistic column should show dashes
        assert _cell(table, 0, 1) == "\u2014"
        assert _cell(table, 1, 1) == "\u2014"

    def test_empty_scenarios_produces_zero_rows(self, table):
        """Empty scenarios dict produces a table with zero rows."""
        table.show_scenario_power_results({}, target_power=80.0)
        assert table._table.rowCount() == 0


# ---------------------------------------------------------------------------
# show_scenario_sample_size_results
# ---------------------------------------------------------------------------


class TestShowScenarioSampleSizeResults:
    """Tests for show_scenario_sample_size_results()."""

    def _make_scenario(self, first_achieved):
        """Helper to build a scenario dict with the expected nested structure."""
        return {"results": {"first_achieved": first_achieved}}

    def test_column_count_and_headers(self, table):
        """Scenario sample size table always has 4 columns."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50}),
            "realistic": self._make_scenario({"x1": 100}),
            "doomer": self._make_scenario({"x1": 200}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0)
        assert table._table.columnCount() == 4
        assert _header(table, 0) == "Tested Variable"
        assert _header(table, 1) == "Optimistic N"
        assert _header(table, 2) == "Realistic N"
        assert _header(table, 3) == "Doomer N"

    def test_all_scenarios_present(self, table):
        """All three scenario columns populated when all present."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50, "x2": 80}),
            "realistic": self._make_scenario({"x1": 100, "x2": 150}),
            "doomer": self._make_scenario({"x1": 200, "x2": 300}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0)
        assert table._table.rowCount() == 2
        assert _cell(table, 0, 0) == "x1"
        assert _cell(table, 0, 1) == "50"
        assert _cell(table, 0, 2) == "100"
        assert _cell(table, 0, 3) == "200"
        assert _cell(table, 1, 0) == "x2"
        assert _cell(table, 1, 1) == "80"
        assert _cell(table, 1, 2) == "150"
        assert _cell(table, 1, 3) == "300"

    def test_not_achieved_with_max_n(self, table):
        """Not-achieved (None) with max_n shows '> N' text."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50}),
            "realistic": self._make_scenario({"x1": None}),
            "doomer": self._make_scenario({"x1": None}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0, max_n=500)
        assert _cell(table, 0, 1) == "50"
        assert _cell(table, 0, 2) == "> 500"
        assert _cell(table, 0, 3) == "> 500"

    def test_not_achieved_without_max_n(self, table):
        """Not-achieved (None) without max_n shows 'Not achieved'."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50}),
            "realistic": self._make_scenario({"x1": None}),
            "doomer": self._make_scenario({"x1": None}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0)
        assert _cell(table, 0, 2) == "Not achieved"
        assert _cell(table, 0, 3) == "Not achieved"

    def test_negative_value_treated_as_not_achieved(self, table):
        """Negative sentinel value treated as not-achieved."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50}),
            "realistic": self._make_scenario({"x1": -1}),
            "doomer": self._make_scenario({"x1": -1}),
        }
        table.show_scenario_sample_size_results(
            scenarios, target_power=80.0, max_n=1000
        )
        assert _cell(table, 0, 2) == "> 1000"
        assert _cell(table, 0, 3) == "> 1000"

    def test_missing_scenario_shows_not_achieved(self, table):
        """Missing scenario (no data) shows not-achieved text."""
        scenarios = {
            "optimistic": self._make_scenario({"x1": 50}),
            # realistic missing
            "doomer": self._make_scenario({"x1": 200}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0, max_n=500)
        assert _cell(table, 0, 1) == "50"
        # realistic missing -> effect not in empty dict -> None -> not achieved
        assert _cell(table, 0, 2) == "> 500"
        assert _cell(table, 0, 3) == "200"

    def test_scenario_order_is_respected(self, table):
        """Scenarios iterate in SCENARIO_ORDER regardless of dict key order."""
        scenarios = {
            "doomer": self._make_scenario({"x1": 300}),
            "optimistic": self._make_scenario({"x1": 50}),
            "realistic": self._make_scenario({"x1": 150}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0)
        assert _cell(table, 0, 1) == "50"  # optimistic
        assert _cell(table, 0, 2) == "150"  # realistic
        assert _cell(table, 0, 3) == "300"  # doomer

    def test_empty_scenarios_produces_zero_rows(self, table):
        """Empty scenarios dict produces a table with zero rows."""
        table.show_scenario_sample_size_results({}, target_power=80.0)
        assert table._table.rowCount() == 0

    def test_effects_from_first_available_scenario(self, table):
        """Effect list comes from the first scenario found in SCENARIO_ORDER."""
        scenarios = {
            # optimistic missing
            "realistic": self._make_scenario({"a": 100, "b": 200}),
            "doomer": self._make_scenario({"a": 250, "b": 400}),
        }
        table.show_scenario_sample_size_results(scenarios, target_power=80.0)
        assert table._table.rowCount() == 2
        assert _cell(table, 0, 0) == "a"
        assert _cell(table, 1, 0) == "b"
        # optimistic column should show "Not achieved"
        assert _cell(table, 0, 1) == "Not achieved"
        assert _cell(table, 1, 1) == "Not achieved"


# ---------------------------------------------------------------------------
# to_csv_lines
# ---------------------------------------------------------------------------


class TestToCsvLines:
    """Tests for to_csv_lines() CSV export."""

    def test_power_results_csv_header(self, table):
        """CSV first line contains column headers."""
        powers = {"x1": 85.0}
        table.show_power_results(powers, target_power=80.0)
        lines = table.to_csv_lines()
        assert len(lines) >= 2  # header + at least 1 data row
        assert "Tested Variable" in lines[0]
        assert "Power (%)" in lines[0]
        assert "Achieved" in lines[0]

    def test_power_results_csv_data(self, table):
        """CSV data row contains the correct values."""
        powers = {"x1": 85.0}
        table.show_power_results(powers, target_power=80.0)
        lines = table.to_csv_lines()
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)
        assert rows[0] == ["Tested Variable", "Power (%)", "Achieved"]
        assert rows[1] == ["x1", "85.0", "Yes"]

    def test_power_results_with_corrected_csv(self, table):
        """CSV includes corrected columns when present."""
        powers = {"x1": 85.0}
        corrected = {"x1": 72.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        lines = table.to_csv_lines()
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)
        assert len(rows[0]) == 5
        assert rows[1] == ["x1", "85.0", "Yes", "72.0", "No"]

    def test_sample_size_csv(self, table):
        """CSV export for sample size results."""
        achieved = {"x1": 150, "x2": None}
        table.show_sample_size_results(achieved, target_power=80.0, max_n=500)
        lines = table.to_csv_lines()
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)
        assert rows[0] == ["Tested Variable", "Required N", "Target Power (%)"]
        assert rows[1] == ["x1", "150", "80.0"]
        assert rows[2] == ["x2", "> 500", "80.0"]

    def test_scenario_power_csv(self, table):
        """CSV export for scenario power results."""
        scenarios = {
            "optimistic": {"results": {"individual_powers": {"x1": 95.0}}},
            "realistic": {"results": {"individual_powers": {"x1": 80.0}}},
            "doomer": {"results": {"individual_powers": {"x1": 60.0}}},
        }
        table.show_scenario_power_results(scenarios, target_power=80.0)
        lines = table.to_csv_lines()
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)
        assert rows[0] == [
            "Tested Variable",
            "Optimistic (%)",
            "Realistic (%)",
            "Doomer (%)",
        ]
        assert rows[1] == ["x1", "95.0", "80.0", "60.0"]

    def test_csv_line_count_matches_rows_plus_header(self, table):
        """Number of CSV lines = 1 header + N data rows."""
        powers = {"x1": 85.0, "x2": 60.0, "x3": 40.0}
        table.show_power_results(powers, target_power=80.0)
        lines = table.to_csv_lines()
        assert len(lines) == 4  # 1 header + 3 rows

    def test_csv_round_trip(self, table):
        """CSV output can be parsed back and matches the original data."""
        powers = {"effect_a": 91.2, "effect_b": 55.8}
        corrected = {"effect_a": 88.0, "effect_b": 50.3}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        lines = table.to_csv_lines()

        # Parse the CSV back
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)

        # Verify header
        assert rows[0] == [
            "Tested Variable",
            "Power (%)",
            "Achieved",
            "Corrected (%)",
            "Corrected Achieved",
        ]

        # Verify data rows match what was set
        assert rows[1][0] == "effect_a"
        assert rows[1][1] == "91.2"
        assert rows[1][2] == "Yes"
        assert rows[1][3] == "88.0"
        assert rows[1][4] == "Yes"

        assert rows[2][0] == "effect_b"
        assert rows[2][1] == "55.8"
        assert rows[2][2] == "No"
        assert rows[2][3] == "50.3"
        assert rows[2][4] == "No"

    def test_csv_with_missing_corrected_dash(self, table):
        """CSV exports em-dash character for missing corrected values."""
        powers = {"x1": 85.0, "x2": 60.0}
        corrected = {"x1": 75.0}
        table.show_power_results(powers, target_power=80.0, powers_corrected=corrected)
        lines = table.to_csv_lines()
        reader = csv.reader(io.StringIO("\n".join(lines)))
        rows = list(reader)
        assert rows[2][3] == "\u2014"  # em-dash for missing x2 corrected
        assert rows[2][4] == "\u2014"

    def test_csv_empty_table(self, table):
        """CSV from an empty table returns just the header (or empty)."""
        # A freshly constructed table has no headers or rows set.
        # After clear() in show_* the column count is reset, but if we never
        # call show_*, the table starts with 0 columns -> empty csv.
        lines = table.to_csv_lines()
        # Single empty line from just the header row (no columns -> empty header)
        assert len(lines) <= 1


# ---------------------------------------------------------------------------
# ResultPanel._save_csv  (end-to-end CSV file export)
# ---------------------------------------------------------------------------


class TestResultPanelSaveCsv:
    """Tests that ResultPanel._save_csv writes a valid CSV with version header."""

    @pytest.fixture
    def panel(self):
        from mcpower_gui.widgets.result_panel import ResultPanel

        result = {"x1": 85.0, "x2": 72.3}
        widget = ResultPanel(
            mode="power",
            result=result,
            target_power=80.0,
            script="# script",
            analysis_params={"sample_size": 100},
        )
        yield widget
        widget.deleteLater()

    def _save_csv_to(self, panel, path):
        """Call _save_csv with mocked file dialog and message box."""
        with (
            patch(
                "mcpower_gui.widgets.result_panel.QFileDialog.getSaveFileName",
                return_value=(path, "CSV files (*.csv)"),
            ),
            patch("mcpower_gui.widgets.result_panel.QMessageBox") as mock_mb,
        ):
            panel._save_csv()
        return mock_mb

    def test_csv_contains_version_header(self, panel):
        """Exported CSV file includes 'Generated by: MCPower v...' header."""
        from mcpower_gui.state import _mcpower_version

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            mock_mb = self._save_csv_to(panel, path)

            mock_mb.warning.assert_not_called()
            assert os.path.exists(path), "_save_csv did not create the file"
            content = open(path, encoding="utf-8-sig").read()
            assert f"MCPower v{_mcpower_version}" in content

    def test_csv_contains_citation(self, panel):
        """Exported CSV file includes the citation line."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            self._save_csv_to(panel, path)

            content = open(path, encoding="utf-8-sig").read()
            assert "Zenodo" in content
