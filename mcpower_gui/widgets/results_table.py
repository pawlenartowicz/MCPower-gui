"""QTableWidget for displaying power analysis results."""

import csv
import io

from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.state import SCENARIO_ORDER


class ResultsTable(QWidget):
    """Table that displays either power-analysis or sample-size results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def show_power_results(
        self,
        powers: dict[str, float],
        target_power: float,
        powers_corrected: dict[str, float] | None = None,
    ):
        """Display find_power results: one row per effect.

        Columns: Effect | Power (%) | Achieved [| Corrected (%) | Corrected Achieved]
        """
        self._table.clear()
        has_corrected = powers_corrected is not None and len(powers_corrected) > 0

        if has_corrected:
            self._table.setColumnCount(5)
            self._table.setHorizontalHeaderLabels(
                [
                    "Tested Variable",
                    "Power (%)",
                    "Achieved",
                    "Corrected (%)",
                    "Corrected Achieved",
                ]
            )
        else:
            self._table.setColumnCount(3)
            self._table.setHorizontalHeaderLabels(
                ["Tested Variable", "Power (%)", "Achieved"]
            )

        self._table.setRowCount(len(powers))

        for row, (name, power) in enumerate(powers.items()):
            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(row, 1, QTableWidgetItem(f"{power:.1f}"))
            achieved = "Yes" if power >= target_power else "No"
            self._table.setItem(row, 2, QTableWidgetItem(achieved))

            if has_corrected:
                corr_power = powers_corrected.get(name)
                if corr_power is not None:
                    self._table.setItem(row, 3, QTableWidgetItem(f"{corr_power:.1f}"))
                    corr_achieved = "Yes" if corr_power >= target_power else "No"
                    self._table.setItem(row, 4, QTableWidgetItem(corr_achieved))
                else:
                    self._table.setItem(row, 3, QTableWidgetItem("—"))
                    self._table.setItem(row, 4, QTableWidgetItem("—"))

        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def show_sample_size_results(
        self,
        first_achieved: dict[str, int | None],
        target_power: float,
        first_achieved_corrected: dict[str, int | None] | None = None,
        max_n: int | None = None,
    ):
        """Display find_sample_size results: one row per effect.

        Columns: Effect | Required N | Target Power (%) [| Corrected N]
        """
        self._table.clear()
        has_corrected = (
            first_achieved_corrected is not None and len(first_achieved_corrected) > 0
        )
        not_achieved_text = f"> {max_n}" if max_n is not None else "Not achieved"

        if has_corrected:
            self._table.setColumnCount(4)
            self._table.setHorizontalHeaderLabels(
                ["Tested Variable", "Required N", "Target Power (%)", "Corrected N"]
            )
        else:
            self._table.setColumnCount(3)
            self._table.setHorizontalHeaderLabels(
                ["Tested Variable", "Required N", "Target Power (%)"]
            )

        self._table.setRowCount(len(first_achieved))

        for row, (name, n) in enumerate(first_achieved.items()):
            self._table.setItem(row, 0, QTableWidgetItem(name))
            n_text = str(n) if n is not None and n >= 0 else not_achieved_text
            self._table.setItem(row, 1, QTableWidgetItem(n_text))
            self._table.setItem(row, 2, QTableWidgetItem(f"{target_power:.1f}"))

            if has_corrected:
                corr_n = first_achieved_corrected.get(name)
                corr_text = (
                    str(corr_n)
                    if corr_n is not None and corr_n >= 0
                    else not_achieved_text
                )
                self._table.setItem(row, 3, QTableWidgetItem(corr_text))

        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def show_scenario_power_results(self, scenarios: dict, target_power: float):
        """Display power results across scenarios.

        Columns: Effect | Optimistic (%) | Realistic (%) | Doomer (%)
        """
        self._table.clear()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Tested Variable", "Optimistic (%)", "Realistic (%)", "Doomer (%)"]
        )

        # Get effect names from first available scenario
        scenario_order = SCENARIO_ORDER
        effects: list[str] = []
        for sname in scenario_order:
            sdata = scenarios.get(sname)
            if sdata:
                powers = sdata.get("results", {}).get("individual_powers", {})
                effects = list(powers.keys())
                break

        self._table.setRowCount(len(effects))
        for row, effect in enumerate(effects):
            self._table.setItem(row, 0, QTableWidgetItem(effect))
            for col, sname in enumerate(scenario_order, start=1):
                sdata = scenarios.get(sname, {})
                powers = sdata.get("results", {}).get("individual_powers", {})
                val = powers.get(effect)
                text = f"{val:.1f}" if val is not None else "—"
                self._table.setItem(row, col, QTableWidgetItem(text))

        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def show_scenario_sample_size_results(
        self, scenarios: dict, target_power: float, max_n: int | None = None
    ):
        """Display sample-size results across scenarios.

        Columns: Effect | Optimistic N | Realistic N | Doomer N
        """
        self._table.clear()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Tested Variable", "Optimistic N", "Realistic N", "Doomer N"]
        )
        not_achieved_text = f"> {max_n}" if max_n is not None else "Not achieved"

        scenario_order = SCENARIO_ORDER
        effects: list[str] = []
        for sname in scenario_order:
            sdata = scenarios.get(sname)
            if sdata:
                achieved = sdata.get("results", {}).get("first_achieved", {})
                effects = list(achieved.keys())
                break

        self._table.setRowCount(len(effects))
        for row, effect in enumerate(effects):
            self._table.setItem(row, 0, QTableWidgetItem(effect))
            for col, sname in enumerate(scenario_order, start=1):
                sdata = scenarios.get(sname, {})
                achieved = sdata.get("results", {}).get("first_achieved", {})
                val = achieved.get(effect)
                text = str(val) if val is not None and val >= 0 else not_achieved_text
                self._table.setItem(row, col, QTableWidgetItem(text))

        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def to_csv_lines(self) -> list[str]:
        """Export current table contents as CSV lines (header + rows)."""
        buf = io.StringIO()
        writer = csv.writer(buf)

        headers = []
        for col in range(self._table.columnCount()):
            item = self._table.horizontalHeaderItem(col)
            headers.append(item.text() if item else "")
        writer.writerow(headers)

        for row in range(self._table.rowCount()):
            cells = []
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                cells.append(item.text() if item else "")
            writer.writerow(cells)

        return buf.getvalue().splitlines()
