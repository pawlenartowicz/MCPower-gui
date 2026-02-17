"""Main application window — tab container, signal routing, worker lifecycle."""

import os

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui import __version__
from mcpower_gui.history_manager import HistoryManager
from mcpower_gui.script_generator import generate_script
from mcpower_gui.state import ModelState
from mcpower_gui.tabs.analysis_tab import AnalysisTab
from mcpower_gui.tabs.model_tab import ModelTab
from mcpower_gui.tabs.results_tab import ResultsTab
from mcpower_gui.update_checker import UpdateChecker
from mcpower_gui.widgets.acknowledgments_dialog import AcknowledgmentsDialog
from mcpower_gui.widgets.documentation_dialog import DocumentationDialog
from mcpower_gui.widgets.history_dialog import HistoryDialog
from mcpower_gui.widgets.progress_dialog import ProgressDialog
from mcpower_gui.widgets.settings_dialog import SettingsDialog
from mcpower_gui.widgets.update_banner import UpdateBanner
from mcpower_gui.worker import AnalysisWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCPower — Monte Carlo Power Analysis")
        self.resize(900, 700)

        self._state = ModelState()
        self._worker: AnalysisWorker | None = None
        self._history = HistoryManager()

        # Menu bar
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_settings)
        self.menuBar().addAction(settings_action)

        history_action = QAction("History", self)
        history_action.triggered.connect(self._open_history)
        self.menuBar().addAction(history_action)

        ack_action = QAction("Acknowledgments", self)
        ack_action.triggered.connect(self._open_acknowledgments)
        self.menuBar().addAction(ack_action)

        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self._open_documentation)
        self.menuBar().addAction(docs_action)

        support_action = QAction("\u2764 Support", self)
        support_action.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://freestylerscientist.pl/support_me/")
            )
        )
        self.menuBar().addAction(support_action)

        # Style the support action with accent color
        for child in self.menuBar().children():
            if (
                hasattr(child, "defaultAction")
                and child.defaultAction() == support_action
            ):
                child.setStyleSheet("color: #e74c3c;")
                break

        # Central widget: update banner + tabs
        self._tabs = QTabWidget()
        self._update_banner = UpdateBanner()
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._update_banner)
        vbox.addWidget(self._tabs)
        self.setCentralWidget(central)

        self._model_tab = ModelTab(self._state)
        self._tabs.addTab(self._model_tab, "Model")

        self._analysis_tab = AnalysisTab(self._state)
        self._tabs.addTab(self._analysis_tab, "Analysis")

        self._results_tab = ResultsTab()
        self._tabs.addTab(self._results_tab, "Results")

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Progress dialog (hidden by default)
        self._progress_dialog = ProgressDialog(self)

        # Connections
        self._progress_dialog.abandon_requested.connect(self._abandon_analysis)
        self._model_tab.model_ready_changed.connect(self._analysis_tab.set_model_ready)
        self._model_tab.available_tests_changed.connect(
            self._analysis_tab.set_available_tests
        )
        self._analysis_tab.run_power_requested.connect(
            lambda params: self._run_analysis("power", params)
        )
        self._analysis_tab.run_sample_size_requested.connect(
            lambda params: self._run_analysis("sample_size", params)
        )
        self._model_tab.model_type_changed.connect(self._analysis_tab.set_model_type)
        self._model_tab.available_factors_changed.connect(
            self._analysis_tab.set_available_factors
        )

        # Background update check (deferred until event loop starts)
        QTimer.singleShot(0, self._start_update_check)

    def _start_update_check(self):
        self._update_checker = UpdateChecker(__version__, parent=self)
        self._update_checker.update_available.connect(self._update_banner.show_update)
        self._update_checker.start()

    def _run_analysis(self, mode: str, params: dict):
        if self._worker is not None and self._worker.isRunning():
            return  # already running

        # Sync model tab state before creating worker
        self._model_tab.sync_state()

        self._analysis_tab.set_running(True)
        label = (
            "Running power analysis..."
            if mode == "power"
            else "Searching for sample size..."
        )
        self._status_bar.showMessage(label)

        self._progress_dialog.start()

        self._worker = AnalysisWorker(self._state, mode, params, parent=self)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.progress.connect(self._on_progress)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.start()

    def _on_progress(self, current: int, total: int):
        self._progress_dialog.update_progress(current, total)

    def _on_finished(self, data: dict):
        self._progress_dialog.stop()
        self._analysis_tab.set_running(False)
        mode = data["mode"]
        result = data["result"]
        state_snapshot = data["state_snapshot"]
        analysis_params = data["analysis_params"]
        data_file_path = data.get("data_file_path")
        target_power = state_snapshot.get("target_power", 80.0)

        script = generate_script(state_snapshot, analysis_params, mode, data_file_path)
        model_type = state_snapshot.get("model_type", "linear_regression")
        self._results_tab.add_result(
            mode,
            result,
            target_power,
            script,
            analysis_params=analysis_params,
            model_type=model_type,
        )
        self._history.save(
            mode,
            result,
            state_snapshot,
            analysis_params,
            data_file_path,
            script,
        )
        self._tabs.setCurrentWidget(self._results_tab)
        self._status_bar.showMessage("Analysis complete", 5000)
        self._worker = None

    def _on_error(self, message: str):
        self._progress_dialog.stop()
        self._analysis_tab.set_running(False)
        self._status_bar.showMessage("Analysis failed")
        QMessageBox.critical(self, "Analysis Error", message)
        self._worker = None

    def _abandon_analysis(self):
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()

    def _on_cancelled(self):
        self._progress_dialog.stop()
        self._analysis_tab.set_running(False)
        self._status_bar.showMessage("Analysis cancelled", 5000)
        self._worker = None

    def _open_settings(self):
        SettingsDialog(self._state, self).exec()

    def _open_acknowledgments(self):
        AcknowledgmentsDialog(self).exec()

    def _open_documentation(self):
        DocumentationDialog(self).exec()

    def _open_history(self):
        dlg = HistoryDialog(self._history, self)
        dlg.load_requested.connect(self._load_from_history)
        dlg.exec()

    def _load_from_history(self, record: dict):
        """Restore full state from a history record."""
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.warning(
                self, "Busy", "An analysis is currently running. Please wait."
            )
            return

        snapshot = record.get("state_snapshot", {})
        analysis_params = record.get("analysis_params", {})
        data_file_path = record.get("data_file_path")
        mode = record.get("mode", "power")
        result = record.get("result", {})
        script = record.get("script", "")
        target_power = snapshot.get("target_power", 80.0)

        # 1. Restore model tab (formula, types, effects, correlations)
        self._model_tab.restore_state(snapshot, data_file_path)

        # 2. Restore state-level settings
        self._state.n_simulations = snapshot.get("n_simulations", 1600)
        self._state.alpha = snapshot.get("alpha", 0.05)
        self._state.target_power = target_power
        self._state.seed = snapshot.get("seed", 2137)
        self._state.max_failed_simulations = snapshot.get(
            "max_failed_simulations", 0.03
        )
        self._state.parallel = snapshot.get("parallel", "mixedmodels")
        self._state.n_cores = snapshot.get(
            "n_cores", max(1, (os.cpu_count() or 4) // 2)
        )
        sc = snapshot.get("scenario_configs")
        if sc is not None:
            self._state.scenario_configs = {k: dict(v) for k, v in sc.items()}

        # 3. Restore analysis tab widgets
        model_type = snapshot.get("model_type", "linear_regression")
        self._analysis_tab.set_model_type(model_type)
        analysis_params_with_tp = dict(analysis_params)
        analysis_params_with_tp["target_power"] = target_power
        self._analysis_tab.restore_params(analysis_params_with_tp)

        # 4. Create result subtab from stored data
        self._results_tab.add_result(
            mode,
            result,
            target_power,
            script,
            analysis_params=analysis_params,
            model_type=model_type,
        )

        # 5. Notify about data file
        if data_file_path:
            QMessageBox.information(
                self,
                "Data File",
                f"This analysis used data from:\n\n{data_file_path}\n\n"
                "Please re-upload the file in the Model tab if you want to "
                "re-run the analysis.",
            )

        # 6. Switch to Results tab
        self._tabs.setCurrentWidget(self._results_tab)
        self._status_bar.showMessage("Loaded from history", 5000)
