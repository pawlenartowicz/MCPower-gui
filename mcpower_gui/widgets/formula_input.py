"""Formula input widget with debounced parsing and validation status."""

from itertools import combinations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from mcpower_gui.theme import current_colors


def _expand_star_term(term: str) -> list[str]:
    """Expand ``x1*x2`` into ``[x1, x2, x1:x2]``."""
    parts = [p.strip() for p in term.split("*")]
    result = list(parts)
    for r in range(2, len(parts) + 1):
        for combo in combinations(parts, r):
            result.append(":".join(combo))
    return result


class FormulaInput(QWidget):
    """Line edit for R-style formulas with live parse feedback.

    Emits formula_changed(dep_var, predictors) after a debounce period
    when the formula parses successfully.
    """

    formula_changed = Signal(str, str, list)  # formula, dep_var, predictors

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.addWidget(QLabel("Formula:"))
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("y = x1 + x2 + x1:x2")
        row.addWidget(self._edit, stretch=1)
        layout.addLayout(row)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        # Debounce timer — 400ms after last keystroke
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._parse)

        self._edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self._timer.start()

    def _parse(self):
        text = self._edit.text().strip()
        if not text:
            self._status.setText("")
            self._status.setStyleSheet("")
            return

        try:
            from mcpower.utils.parsers import _parse_equation

            dep_var, formula_part, _random_effects = _parse_equation(text)

            # Extract predictors from formula part (handles interactions and * notation)
            raw_terms = [t.strip() for t in formula_part.split("+") if t.strip()]
            predictors = []
            for term in raw_terms:
                if "*" in term:
                    predictors.extend(_expand_star_term(term))
                else:
                    predictors.append(term)
            # Deduplicate preserving order
            seen: set[str] = set()
            predictors = [p for p in predictors if not (p in seen or seen.add(p))]

            self._status.setText(
                f"Dependent: {dep_var} | Predictors: {', '.join(predictors)}"
            )
            self._status.setStyleSheet(f"color: {current_colors()['success']};")
            self.formula_changed.emit(text, dep_var, predictors)

        except Exception as exc:
            self._status.setText(f"Parse error: {exc}")
            self._status.setStyleSheet(f"color: {current_colors()['error']};")

    def set_formula(self, text: str):
        """Set formula text and parse immediately (no debounce)."""
        self._edit.setText(text)
        self._timer.stop()
        self._parse()

    def text(self) -> str:
        return self._edit.text().strip()
