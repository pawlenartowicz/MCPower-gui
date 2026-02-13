"""Dynamic effects editor — one row per predictor with S/M/L helper buttons."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


_EFFECT_SIZES = {
    "continuous": {"S": 0.1, "M": 0.25, "L": 0.4},
    "binary": {"S": 0.2, "M": 0.5, "L": 0.8},
    "factor": {"S": 0.2, "M": 0.5, "L": 0.8},
}

_LONG_NAMES = {"S": "small", "M": "medium", "L": "large"}


class EffectsEditor(QWidget):
    """Form that creates one effect-size row per predictor.

    Each row: [label] [spinbox] [\u2212] [S] [M] [L]
    Buttons expand to full text (small/medium/large) when space allows.

    Call set_predictors() to rebuild the rows. Emits effects_changed
    whenever any value changes.
    """

    effects_changed = Signal(dict)  # {predictor_name: effect_size}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, QDoubleSpinBox] = {}
        self._predictor_types: dict[str, str] = {}
        self._buttons: list[tuple[QPushButton, str, str]] = []  # (btn, short, long)
        self._updating_text = False

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_predictors(
        self,
        predictors: list[str],
        current_effects: dict[str, float],
        predictor_types: dict[str, str] | None = None,
    ):
        """Rebuild rows for a new predictor list, preserving existing values."""
        self._predictor_types = predictor_types or {}
        self._buttons.clear()

        # Clear old rows
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()

        for name in predictors:
            value = current_effects.get(name, 0.0)
            vtype = self._predictor_types.get(name, "continuous")
            row = self._make_row(name, value, vtype)
            self._layout.addWidget(row)

    def _make_row(self, name: str, value: float, vtype: str) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 2, 0, 2)

        label = QLabel(name)
        label.setFixedWidth(120)
        h.addWidget(label)

        spin = QDoubleSpinBox()
        spin.setRange(-2.0, 2.0)
        spin.setSingleStep(0.05)
        spin.setDecimals(2)
        spin.setValue(value)
        spin.setFixedWidth(80)
        h.addWidget(spin)

        # Sign toggle button (fixed width)
        sign_btn = QPushButton("\u2212")
        sign_btn.setFixedWidth(28)
        sign_btn.setToolTip("Toggle sign")
        sign_btn.clicked.connect(lambda _, s=spin: self._toggle_sign(s))
        h.addWidget(sign_btn)

        # S / M / L buttons — expand to small/medium/large when space allows
        sizes = _EFFECT_SIZES.get(vtype, _EFFECT_SIZES["continuous"])
        for label_text, size_val in sizes.items():
            long_text = _LONG_NAMES[label_text]
            btn = QPushButton(label_text)
            btn.setMinimumWidth(28)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setToolTip(f"{long_text} effect = {size_val}")
            btn.clicked.connect(
                lambda _, s=spin, sv=size_val: self._set_effect_size(s, sv)
            )
            h.addWidget(btn)
            self._buttons.append((btn, label_text, long_text))

        self._rows[name] = spin
        spin.valueChanged.connect(lambda _: self._emit())

        return row

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_button_texts()

    def _update_button_texts(self):
        if self._updating_text or not self._buttons:
            return
        self._updating_text = True
        for btn, short, long in self._buttons:
            fm = btn.fontMetrics()
            needed = fm.horizontalAdvance(long) + 16
            if btn.width() >= needed:
                if btn.text() != long:
                    btn.setText(long)
            else:
                if btn.text() != short:
                    btn.setText(short)
        self._updating_text = False

    def _toggle_sign(self, spin: QDoubleSpinBox):
        """Negate the current value."""
        spin.setValue(-spin.value())

    def _set_effect_size(self, spin: QDoubleSpinBox, size: float):
        """Set effect size, preserving the current sign."""
        current = spin.value()
        sign = -1 if current < 0 else 1
        spin.setValue(sign * abs(size))

    def _emit(self):
        self.effects_changed.emit(self.get_effects())

    def get_effects(self) -> dict[str, float]:
        return {name: spin.value() for name, spin in self._rows.items()}
