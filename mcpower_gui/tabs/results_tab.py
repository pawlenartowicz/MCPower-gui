"""Results tab — closeable subtabs for each analysis run."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QStackedLayout, QTabWidget, QWidget

from mcpower_gui.widgets.result_panel import ResultPanel


class ResultsTab(QWidget):
    """Closeable QTabWidget with a placeholder shown when empty.

    Call ``add_result()`` to create a new subtab for each analysis run.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._stack = QStackedLayout(self)

        # Placeholder (shown when no tabs)
        self._placeholder = QLabel("Run an analysis to see results here.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stack.addWidget(self._placeholder)

        # Tab widget (shown when at least one result exists)
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._stack.addWidget(self._tab_widget)

        # Track creation time per tab widget id for naming
        self._tab_times: dict[int, datetime] = {}

        # Timer to update tab name suffixes every 60s
        self._name_timer = QTimer(self)
        self._name_timer.setInterval(60_000)
        self._name_timer.timeout.connect(self._update_tab_names)

        self._stack.setCurrentWidget(self._placeholder)

    def add_result(
        self,
        mode: str,
        result: dict,
        target_power: float,
        script: str,
        analysis_params: dict | None = None,
        model_type: str = "linear_regression",
    ) -> ResultPanel:
        """Create a ResultPanel subtab and select it.

        Returns the created panel.
        """
        panel = ResultPanel(
            mode,
            result,
            target_power,
            script,
            analysis_params=analysis_params,
            parent=self,
        )
        now = datetime.now()
        type_prefix = "A" if model_type == "anova" else "lm"
        mode_prefix = "FP" if mode == "power" else "FSS"
        tab_name = f"{type_prefix}_{mode_prefix} | {now.strftime('%H:%M')}"

        idx = self._tab_widget.addTab(panel, tab_name)
        self._tab_times[id(panel)] = now
        self._tab_widget.setCurrentIndex(idx)

        self._stack.setCurrentWidget(self._tab_widget)
        if not self._name_timer.isActive():
            self._name_timer.start()

        return panel

    def _close_tab(self, index: int):
        """Remove a subtab and clean up."""
        widget = self._tab_widget.widget(index)
        if widget is not None:
            self._tab_times.pop(id(widget), None)
            self._tab_widget.removeTab(index)
            widget.deleteLater()

        if self._tab_widget.count() == 0:
            self._stack.setCurrentWidget(self._placeholder)
            self._name_timer.stop()

    def _update_tab_names(self):
        """Update tab name suffixes with elapsed time."""
        now = datetime.now()
        for i in range(self._tab_widget.count()):
            widget = self._tab_widget.widget(i)
            if widget is None:
                continue
            created = self._tab_times.get(id(widget))
            if created is None:
                continue

            text = self._tab_widget.tabText(i)
            # Strip any existing suffix
            base = text.split(" (")[0]

            elapsed = (now - created).total_seconds()
            if elapsed < 60:
                self._tab_widget.setTabText(i, base)
            elif elapsed < 3600:
                minutes = int(elapsed // 60)
                self._tab_widget.setTabText(i, f"{base} ({minutes}m ago)")
            else:
                hours = int(elapsed // 3600)
                self._tab_widget.setTabText(i, f"{base} ({hours}h ago)")
