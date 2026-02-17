"""Single-result subtab: header + plots + table + script + export buttons."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mcpower import __version__ as _mcpower_version

from mcpower_gui.state import SCENARIO_ORDER
from mcpower_gui.theme import current_colors
from mcpower_gui.widgets.power_bar_chart import PowerBarChart
from mcpower_gui.widgets.power_curve_plot import PowerCurvePlot
from mcpower_gui.widgets.results_table import ResultsTable

_CITATION = "Lenartowicz, P. (2025). MCPower: Monte Carlo Power Analysis for Statistical Models. Zenodo. DOI: 10.5281/zenodo.16502734"

_SCENARIO_TITLES = {
    "optimistic": "Optimistic",
    "realistic": "Realistic",
    "doomer": "Doomer",
}


class ResultPanel(QWidget):
    """Content widget for a single results subtab.

    Parameters
    ----------
    mode : str
        "power" or "sample_size".
    result : dict
        MCPower result dict.
    target_power : float
        Target power percentage.
    script : str
        Replication Python script text.
    analysis_params : dict | None
        The analysis parameters used for this run.
    """

    def __init__(
        self,
        mode: str,
        result: dict,
        target_power: float,
        script: str,
        analysis_params: dict | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._mode = mode
        self._result = result
        self._target_power = target_power
        self._script = script
        self._analysis_params = analysis_params or {}
        self._bar_charts: list[PowerBarChart] = []
        self._curve_plots: list[PowerCurvePlot] = []

        is_scenario = "scenarios" in result

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)

        # ── Header ──────────────────────────────────────────────
        header_text = self._build_header_text(result, mode)
        header = QLabel(header_text)
        header.setWordWrap(True)
        header.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # ── Build layout based on scenario on/off ───────────────
        if is_scenario:
            self._build_scenario_view(layout, result, mode, target_power)
        else:
            self._build_single_view(layout, result, mode, target_power)

        # ── Spacing ──────────────────────────────────────────────
        layout.addSpacing(16)

        # ── Separator ────────────────────────────────────────────
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        layout.addSpacing(8)

        # ── Replication Script ──────────────────────────────────
        script_label = QLabel("Replication Script:")
        script_label.setStyleSheet("font-weight: bold; margin-top: 6px;")
        layout.addWidget(script_label)

        self._script_edit = QTextEdit()
        self._script_edit.setReadOnly(True)
        self._script_edit.setPlainText(script)
        self._script_edit.setMaximumHeight(150)
        colors = current_colors()
        self._script_edit.setStyleSheet(
            f"font-family: monospace; font-size: 11px; color: {colors['script_fg']}; background: {colors['script_bg']};"
        )
        layout.addWidget(self._script_edit)

        # ── Export buttons ──────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_copy = QPushButton("Copy Script")
        btn_copy.clicked.connect(self._copy_script)
        btn_row.addWidget(btn_copy)

        btn_csv = QPushButton("Save CSV")
        btn_csv.clicked.connect(self._save_csv)
        btn_row.addWidget(btn_csv)

        btn_jpg = QPushButton("Save Plots as JPG")
        btn_jpg.clicked.connect(self._save_plots)
        btn_row.addWidget(btn_jpg)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Header builder ────────────────────────────────────────────

    def _build_header_text(self, result: dict, mode: str) -> str:
        """Build header: mode | model formula | test formula | N info | scenarios | correction."""
        model_info = result.get("model", {})
        gen_formula = model_info.get("formula", "")
        test_formula = self._analysis_params.get("test_formula", "")
        correction = self._analysis_params.get("correction", "")

        mode_label = "Find Power" if mode == "power" else "Find Sample Size"
        parts = [mode_label]

        if gen_formula:
            parts.append(f"model formula: {gen_formula}")
        if test_formula:
            parts.append(f"test formula: {test_formula}")

        if mode == "power":
            n = self._analysis_params.get("sample_size", "?")
            parts.append(f"N = {n}")
        else:
            from_s = self._analysis_params.get("ss_from", "?")
            to_s = self._analysis_params.get("ss_to", "?")
            by_s = self._analysis_params.get("ss_by", "?")
            parts.append(f"from {from_s} to {to_s}, by {by_s}")

        if self._analysis_params.get("scenarios", False):
            parts.append("scenarios")

        if correction:
            parts.append(f"correction: {correction}")

        return " | ".join(parts)

    # ── Plot / table helpers ────────────────────────────────────────

    def _add_plot(
        self,
        layout: QVBoxLayout,
        results: dict,
        mode: str,
        target_power: float,
        title: str | None = None,
    ):
        """Create and add a bar chart (power) or curve plot (sample_size)."""
        if mode == "power":
            chart = PowerBarChart()
            if title:
                chart._plot.setTitle(title)
            powers = results.get("individual_powers", {})
            if powers:
                chart.update_chart(powers, target_power)
            layout.addWidget(chart, stretch=2)
            self._bar_charts.append(chart)
        else:
            curve = PowerCurvePlot()
            if title:
                curve._plot.setTitle(title)
            sample_sizes = results.get("sample_sizes_tested", [])
            powers_by_test = results.get("powers_by_test", {})
            first_achieved = results.get("first_achieved", {})
            if sample_sizes:
                curve.update_plot(
                    sample_sizes, powers_by_test, first_achieved, target_power
                )
            layout.addWidget(curve, stretch=2)
            self._curve_plots.append(curve)

    def _add_results_table(
        self,
        layout: QVBoxLayout,
        results: dict,
        mode: str,
        target_power: float,
        max_n: int | None = None,
    ) -> ResultsTable:
        """Create, populate, and add a results table. Returns the table."""
        table = ResultsTable()
        layout.addWidget(table, stretch=1)
        if mode == "power":
            powers = results.get("individual_powers", {})
            powers_corrected = results.get("individual_powers_corrected")
            if powers:
                table.show_power_results(
                    powers, target_power, powers_corrected=powers_corrected
                )
        else:
            first_achieved = results.get("first_achieved", {})
            first_achieved_corrected = results.get("first_achieved_corrected")
            if first_achieved:
                table.show_sample_size_results(
                    first_achieved,
                    target_power,
                    first_achieved_corrected=first_achieved_corrected,
                    max_n=max_n,
                )
        return table

    # ── Single (non-scenario) view ────────────────────────────────

    def _build_single_view(
        self, layout: QVBoxLayout, result: dict, mode: str, target_power: float
    ):
        """Non-scenario: one plot + one table."""
        results = result.get("results", {})
        max_n = self._analysis_params.get("ss_to")
        self._add_plot(layout, results, mode, target_power)
        self._results_table = self._add_results_table(
            layout, results, mode, target_power, max_n
        )

    # ── Scenario view ─────────────────────────────────────────────

    def _build_scenario_view(
        self, layout: QVBoxLayout, result: dict, mode: str, target_power: float
    ):
        """Scenario mode: QTabWidget with 3 tabs (Optimistic/Realistic/Doomer)."""
        scenarios = result.get("scenarios", {})
        max_n = self._analysis_params.get("ss_to")
        has_correction = bool(self._analysis_params.get("correction", ""))

        scenario_tabs = QTabWidget()

        for sname in SCENARIO_ORDER:
            sdata = scenarios.get(sname, {})
            sresults = sdata.get("results", {})
            title = _SCENARIO_TITLES.get(sname, sname.title())

            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            self._add_plot(tab_layout, sresults, mode, target_power, title=title)
            if has_correction:
                self._add_results_table(tab_layout, sresults, mode, target_power, max_n)
            scenario_tabs.addTab(tab, title)

        layout.addWidget(scenario_tabs, stretch=3)

        # Combined summary table (all scenarios side by side)
        self._results_table = ResultsTable()
        layout.addWidget(self._results_table, stretch=1)

        if mode == "power":
            self._results_table.show_scenario_power_results(scenarios, target_power)
        else:
            self._results_table.show_scenario_sample_size_results(
                scenarios, target_power, max_n=max_n
            )

    # ── Export actions ──────────────────────────────────────────

    def _copy_script(self):
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._script)

    def _save_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "results.csv", "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            import csv as _csv
            import io as _io

            buf = _io.StringIO()
            writer = _csv.writer(buf)
            writer.writerow(["Generated by:", f"MCPower v{_mcpower_version}"])
            writer.writerow(["Cite:", _CITATION])
            writer.writerow([])
            meta_lines = buf.getvalue().splitlines()

            lines = meta_lines + self._results_table.to_csv_lines()
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as exc:
            QMessageBox.warning(self, "Save Error", str(exc))

    def _save_plots(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Plots", "power_plots.jpg", "JPEG files (*.jpg)"
        )
        if not path:
            return
        try:
            import pyqtgraph.exporters as exporters

            base = path.rsplit(".", 1)[0] if "." in path else path

            for i, chart in enumerate(self._bar_charts):
                suffix = f"_bar_{i}" if len(self._bar_charts) > 1 else "_bar"
                exporter = exporters.ImageExporter(chart._plot.plotItem)
                exporter.parameters()["width"] = 800
                exporter.export(f"{base}{suffix}.jpg")

            for i, curve in enumerate(self._curve_plots):
                suffix = f"_curve_{i}" if len(self._curve_plots) > 1 else "_curve"
                exporter = exporters.ImageExporter(curve._plot.plotItem)
                exporter.parameters()["width"] = 800
                exporter.export(f"{base}{suffix}.jpg")
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
