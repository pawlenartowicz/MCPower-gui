"""Formula input widget with debounced parsing and validation status."""

from itertools import combinations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui.theme import current_colors

EXAMPLES = [
    (
        "Two predictors",
        "score = study_hours + received_help",
        {"received_help": {"type": "binary", "proportion": 0.5}},
    ),
    (
        "With interaction",
        "score = study_hours + received_help + study_hours:received_help",
        {"received_help": {"type": "binary", "proportion": 0.5}},
    ),
    (
        "Mixed model",
        "score = study_hours + received_help + (1|school)",
        {"received_help": {"type": "binary", "proportion": 0.5}},
    ),
]


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

    Emits formula_changed(formula, dep_var, predictors, random_effects) after
    a debounce period when the formula parses successfully. random_effects is
    a list of dicts from the parser (empty list for OLS formulas).
    """

    formula_changed = Signal(
        str, str, list, list
    )  # formula, dep_var, predictors, random_effects
    types_hinted = Signal(dict)  # suggested variable types from example selection

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.addWidget(QLabel("Formula:"))
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("score = study_hours + received_help")
        row.addWidget(self._edit, stretch=1)
        layout.addLayout(row)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        # Example buttons
        examples_row = QHBoxLayout()
        examples_label = QLabel("Examples:")
        examples_label.setStyleSheet(
            f"color: {current_colors()['muted']}; font-size: 11px;"
        )
        examples_row.addWidget(examples_label)

        for label_text, formula_text, types_hint in EXAMPLES:
            btn = QPushButton(label_text)
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ color: {current_colors()['muted']}; font-size: 11px; "
                f"text-decoration: underline; border: none; padding: 1px 4px; }}"
                f"QPushButton:hover {{ color: {current_colors()['success']}; }}"
            )
            btn.clicked.connect(
                lambda _, f=formula_text, t=types_hint: self.load_example(f, t)
            )
            examples_row.addWidget(btn)

        examples_row.addStretch()
        layout.addLayout(examples_row)

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
            self.formula_changed.emit("", "", [], [])
            return

        try:
            from mcpower.utils.parsers import _parse_equation

            dep_var, formula_part, random_effects = _parse_equation(text)

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

            # Build status text (multi-line)
            lines = [f"✓ Dependent: {dep_var}"]
            lines.append(f"  Predictors: {', '.join(predictors)}")
            if random_effects:
                re_strs = []
                for re in random_effects:
                    gv = re["grouping_var"]
                    if re["type"] == "random_slope":
                        slopes = ", ".join(re.get("slope_vars", []))
                        re_strs.append(f"(1 + {slopes}|{gv})")
                    elif re.get("parent_var"):
                        re_strs.append(f"(1|{re['parent_var']}/{gv})")
                    else:
                        re_strs.append(f"(1|{gv})")
                lines.append(f"  Random effects: {', '.join(re_strs)}")
            self._status.setText("\n".join(lines))
            self._status.setStyleSheet(f"color: {current_colors()['success']};")
            self.formula_changed.emit(text, dep_var, predictors, random_effects)

        except Exception as exc:
            self._status.setText(f"Parse error: {exc}")
            self._status.setStyleSheet(f"color: {current_colors()['error']};")

    def load_example(self, formula: str, types_hint: dict):
        """Load an example formula, emitting type hints before parsing."""
        if types_hint:
            self.types_hinted.emit(types_hint)
        self.set_formula(formula)

    def set_formula(self, text: str):
        """Set formula text and parse immediately (no debounce)."""
        self._edit.setText(text)
        self._timer.stop()
        self._parse()

    def text(self) -> str:
        return self._edit.text().strip()
