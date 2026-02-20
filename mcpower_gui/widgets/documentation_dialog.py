"""Documentation dialog — sidebar navigation + markdown viewer."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui._resources import resource_path

# (display_name, filename_or_None)  — None = section header
_PAGES: list[tuple[str, str | None]] = [
    ("Overview", None),
    ("About MCPower GUI", "overview.md"),
    ("Key Concepts", "key_concepts.md"),
    ("Citation", "citation.md"),
    ("Model", None),
    ("Input Mode", "input_mode.md"),
    ("Use Your Data", "use_your_data.md"),
    ("Model Formula", "model_formula.md"),
    ("Variable Types", "variable_types.md"),
    ("ANOVA Factors", "anova_factors.md"),
    ("Effect Sizes", "effect_sizes.md"),
    ("Cluster Configuration", "cluster_config.md"),
    ("Correlations", "correlations.md"),
    ("Data Preparation", "data_preparation.md"),
    ("Mixed Models Guide", "mixed_models_guide.md"),
    ("Analysis", None),
    ("Common Settings", "common_settings.md"),
    ("Post Hoc Comparisons", "post_hoc.md"),
    ("Find Power", "find_power.md"),
    ("Find Sample Size", "find_sample_size.md"),
    ("Results", None),
    ("Understanding Results", "results.md"),
    ("Other", None),
    ("General Settings", "general_settings.md"),
    ("Scenario Settings", "scenario_settings.md"),
]

_ROLE_IS_HEADER = Qt.ItemDataRole.UserRole + 1
_CHILD_INDENT = 16


class _SidebarDelegate(QStyledItemDelegate):
    """Custom delegate that indents child pages and styles section headers."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._header_font: QFont | None = None

    def paint(self, painter, option, index):
        is_header = index.data(_ROLE_IS_HEADER)
        if is_header:
            # Section header — bold, muted foreground, no highlight
            painter.save()
            opt = QStyleOptionViewItem(option)
            # Never draw selection highlight for headers
            opt.state &= ~QStyle.StateFlag.State_Selected
            opt.state &= ~QStyle.StateFlag.State_MouseOver

            style = opt.widget.style() if opt.widget else None
            if style:
                style.drawPrimitive(
                    QStyle.PrimitiveElement.PE_PanelItemViewItem,
                    opt,
                    painter,
                    opt.widget,
                )

            if self._header_font is None:
                self._header_font = QFont(opt.font)
                self._header_font.setBold(True)
                self._header_font.setPointSizeF(opt.font.pointSizeF() * 0.85)
                self._header_font.setCapitalization(QFont.Capitalization.AllUppercase)
            painter.setFont(self._header_font)
            muted = opt.palette.color(QPalette.ColorRole.PlaceholderText)
            painter.setPen(muted)
            text_rect = opt.rect.adjusted(6, 0, 0, 0)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                index.data(),
            )
            painter.restore()
        else:
            # Child page — indent
            opt = QStyleOptionViewItem(option)
            opt.rect = opt.rect.adjusted(_CHILD_INDENT, 0, 0, 0)
            super().paint(painter, opt, index)

    def sizeHint(self, option, index):
        is_header = index.data(_ROLE_IS_HEADER)
        base = super().sizeHint(option, index)
        if is_header:
            # Taller to create visual separation before each section
            return QSize(base.width(), base.height() + 8)
        return base


def _load_doc_page(filename: str) -> str:
    return resource_path("docs", filename).read_text(encoding="utf-8")


class DocumentationDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, initial_page: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Documentation")
        self.resize(780, 560)

        root = QVBoxLayout(self)

        body = QHBoxLayout()

        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setItemDelegate(_SidebarDelegate(self._sidebar))

        for display_name, filename in _PAGES:
            item = QListWidgetItem(display_name)
            if filename is None:
                # Section header — non-selectable
                item.setData(_ROLE_IS_HEADER, True)
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            else:
                item.setData(_ROLE_IS_HEADER, False)
            self._sidebar.addItem(item)

        body.addWidget(self._sidebar)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        body.addWidget(self._browser, stretch=1)

        root.addLayout(body, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        root.addWidget(buttons)

        self._sidebar.currentRowChanged.connect(self._on_page_changed)

        # Find start row — match by filename
        start_row = self._first_selectable_row()
        if initial_page:
            for i, (_, filename) in enumerate(_PAGES):
                if filename == initial_page:
                    start_row = i
                    break
        self._sidebar.setCurrentRow(start_row)

    def _first_selectable_row(self) -> int:
        """Return the index of the first selectable (non-header) row."""
        for i, (_, filename) in enumerate(_PAGES):
            if filename is not None:
                return i
        return 0

    def _on_page_changed(self, row: int):
        if 0 <= row < len(_PAGES):
            _, filename = _PAGES[row]
            if filename is not None:
                text = _load_doc_page(filename)
                self._browser.setMarkdown(text)
