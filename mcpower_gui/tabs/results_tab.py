"""Results tab — closeable subtabs for each analysis run."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QMenu,
    QStackedLayout,
    QTabWidget,
    QWidget,
)

from mcpower_gui.history_manager import HistoryManager
from mcpower_gui.theme import current_colors
from mcpower_gui.widgets.result_panel import ResultPanel


class ResultsTab(QWidget):
    """Closeable QTabWidget with a placeholder shown when empty.

    Call ``add_result()`` to create a new subtab for each analysis run.
    """

    def __init__(
        self,
        history_manager: HistoryManager | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._history_manager = history_manager
        self._tab_record_ids: dict[int, str] = {}  # id(widget) → record_id
        self._tab_base_names: dict[int, str] = {}  # id(widget) → base tab name (no suffix)

        self._stack = QStackedLayout(self)

        # Placeholder (shown when no tabs)
        self._placeholder = QLabel(
            "┌─────────┐    ┌──────────┐    ┌─────────┐\n"
            "│  Model  │  → │ Analysis │  → │ Results │\n"
            "└─────────┘    └──────────┘    └─────────┘\n"
            "\n"
            "Define your model in the Model tab, configure\n"
            "analysis settings, then run to see results here."
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colors = current_colors()
        self._placeholder.setStyleSheet(
            f"color: {colors['muted']}; font-family: monospace; font-size: 12px;"
        )
        self._stack.addWidget(self._placeholder)

        # Tab widget (shown when at least one result exists)
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tab_widget.customContextMenuRequested.connect(self._show_context_menu)
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
        record_id: str | None = None,
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
        # Build descriptive tab name
        formula = analysis_params.get("_formula", "") if analysis_params else ""
        if model_type == "anova":
            prefix = "ANOVA"
        else:
            prefix = formula if formula else "lm"
        # Truncate formula to ~30 chars
        if len(prefix) > 30:
            prefix = prefix[:27] + "..."

        if mode == "power":
            ss = analysis_params.get("sample_size", "?") if analysis_params else "?"
            mode_suffix = f"Power N={ss}"
        else:
            ss_from = analysis_params.get("ss_from", "?") if analysis_params else "?"
            ss_to = analysis_params.get("ss_to", "?") if analysis_params else "?"
            mode_suffix = f"SS {ss_from}\u2192{ss_to}"

        tab_name = f"{prefix} | {mode_suffix} | {now.strftime('%H:%M')}"

        idx = self._tab_widget.addTab(panel, tab_name)
        self._tab_times[id(panel)] = now
        self._tab_base_names[id(panel)] = tab_name
        if record_id is not None:
            self._tab_record_ids[id(panel)] = record_id
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
            self._tab_base_names.pop(id(widget), None)
            self._tab_record_ids.pop(id(widget), None)
            self._tab_widget.removeTab(index)
            widget.deleteLater()

        if self._tab_widget.count() == 0:
            self._stack.setCurrentWidget(self._placeholder)
            self._name_timer.stop()

    def _show_context_menu(self, pos):
        """Show right-click context menu on tab bar."""
        tab_bar = self._tab_widget.tabBar()
        index = tab_bar.tabAt(pos)
        if index < 0:
            return

        menu = QMenu(self)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_tab(index))
        menu.addAction(rename_action)

        menu.addSeparator()

        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self._close_tab(index))
        menu.addAction(close_action)

        if self._tab_widget.count() > 1:
            close_others = QAction("Close Others", self)
            close_others.triggered.connect(lambda: self._close_others(index))
            menu.addAction(close_others)

        close_all = QAction("Close All", self)
        close_all.triggered.connect(self._close_all)
        menu.addAction(close_all)

        menu.exec(tab_bar.mapToGlobal(pos))

    def _rename_tab(self, index: int):
        """Rename a tab via input dialog and persist the name to history."""
        widget = self._tab_widget.widget(index)
        current_base = (
            self._tab_base_names.get(id(widget))
            if widget is not None
            else self._tab_widget.tabText(index)
        )
        new_name, ok = QInputDialog.getText(
            self, "Rename Tab", "New name:", text=current_base
        )
        if ok and new_name.strip():
            new_name = new_name.strip()
            self._tab_widget.setTabText(index, new_name)
            if widget is not None:
                self._tab_base_names[id(widget)] = new_name
                if self._history_manager is not None:
                    record_id = self._tab_record_ids.get(id(widget))
                    if record_id is not None:
                        self._history_manager.update_custom_name(record_id, new_name)

    def _close_others(self, keep_index: int):
        """Close all tabs except the one at keep_index.

        Iterates in reverse so that removing higher-indexed tabs does not
        shift the position of ``keep_index``.
        """
        for i in range(self._tab_widget.count() - 1, -1, -1):
            if i != keep_index:
                self._close_tab(i)

    def _close_all(self):
        """Close all tabs."""
        for i in range(self._tab_widget.count() - 1, -1, -1):
            self._close_tab(i)

    def _update_tab_names(self):
        """Update tab name suffixes with elapsed time."""
        now = datetime.now()
        for i in range(self._tab_widget.count()):
            widget = self._tab_widget.widget(i)
            if widget is None:
                continue
            created = self._tab_times.get(id(widget))
            base = self._tab_base_names.get(id(widget))
            if created is None or base is None:
                continue

            elapsed = (now - created).total_seconds()
            if elapsed < 60:
                self._tab_widget.setTabText(i, base)
            elif elapsed < 3600:
                minutes = int(elapsed // 60)
                self._tab_widget.setTabText(i, f"{base} ({minutes}m ago)")
            else:
                hours = int(elapsed // 3600)
                self._tab_widget.setTabText(i, f"{base} ({hours}h ago)")
