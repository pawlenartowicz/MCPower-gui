"""Declarative tip engine — evaluates YAML rules against UI state."""

from __future__ import annotations

__all__ = ["TipEngine", "ResolvedTip"]

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedTip:
    """A tip that matched the current state, ready to render."""

    id: str
    text: str
    style: str  # "done" | "next" | "optional" | "normal"
    tip_type: str  # "text" | "formula_examples"


class TipEngine:
    """Evaluate tip rules against state and return matching tips.

    Each rule is a dict with keys: id, tab, text, style, priority,
    conditions, and optional type.

    Conditions use AND logic — all must match. Supported operators:
    - Exact match: ``key: value``
    - Not empty: ``key: "!empty"``
    - Not equal: ``key: "!value"``
    - Greater-or-equal: ``key: ">=N"``
    """

    def __init__(self, rules: list[dict]) -> None:
        self._rules = rules

    def evaluate(self, state: dict) -> list[ResolvedTip]:
        """Return tips matching *state*, sorted by priority."""
        tab = state.get("tab", "")
        matched: list[tuple[int, ResolvedTip]] = []

        for rule in self._rules:
            if rule.get("tab", "") != tab:
                continue
            if not self._matches(rule.get("conditions", {}), state):
                continue

            text = rule.get("text", "")
            try:
                text = text.format_map(_SafeFormatMap(state))
            except (KeyError, ValueError):
                pass

            tip = ResolvedTip(
                id=rule["id"],
                text=text,
                style=rule.get("style", "normal"),
                tip_type=rule.get("type", "text"),
            )
            matched.append((rule.get("priority", 999), tip))

        matched.sort(key=lambda pair: pair[0])
        return [tip for _, tip in matched]

    @staticmethod
    def _matches(conditions: dict, state: dict) -> bool:
        """Check if all conditions match the state."""
        for key, expected in conditions.items():
            if key not in state:
                return False
            actual = state[key]

            if isinstance(expected, bool):
                if actual != expected:
                    return False
            elif isinstance(expected, str):
                if expected == "":
                    if actual != "":
                        return False
                elif expected == "!empty":
                    if not actual:
                        return False
                elif expected.startswith(">="):
                    threshold = int(expected[2:])
                    if not isinstance(actual, (int, float)) or actual < threshold:
                        return False
                elif expected.startswith("!"):
                    if str(actual) == expected[1:]:
                        return False
                else:
                    if str(actual) != expected:
                        return False
            elif isinstance(expected, (int, float)):
                if actual != expected:
                    return False
            else:
                if actual != expected:
                    return False
        return True


class _SafeFormatMap(dict):
    """Dict subclass that returns '{key}' for missing keys instead of raising."""

    def __init__(self, mapping: dict) -> None:
        super().__init__(mapping)

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
