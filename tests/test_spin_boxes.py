"""Tests for SpinBox, DoubleSpinBox, and normalize_proportion_spinboxes."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from mcpower_gui.widgets.spin_boxes import (
    DoubleSpinBox,
    SpinBox,
    normalize_proportion_spinboxes,
)

_app = QApplication.instance() or QApplication([])


def _make_wheel_event(delta: int = 120) -> QWheelEvent:
    """Create a synthetic QWheelEvent with the given vertical angle delta."""
    return QWheelEvent(
        QPointF(0, 0),  # pos
        QPointF(0, 0),  # globalPos
        QPoint(0, 0),  # pixelDelta
        QPoint(0, delta),  # angleDelta
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,  # inverted
    )


# ---------------------------------------------------------------------------
# SpinBox (integer)
# ---------------------------------------------------------------------------


class TestSpinBox:
    """Tests for the custom SpinBox (QSpinBox subclass)."""

    def test_instantiation(self):
        """SpinBox can be created without arguments."""
        spin = SpinBox()
        assert spin is not None

    def test_is_qspinbox(self):
        """SpinBox is a subclass of QSpinBox."""
        from PySide6.QtWidgets import QSpinBox

        spin = SpinBox()
        assert isinstance(spin, QSpinBox)

    def test_focus_policy_is_strong_focus(self):
        """SpinBox sets focus policy to StrongFocus on init."""
        spin = SpinBox()
        assert spin.focusPolicy() == Qt.FocusPolicy.StrongFocus

    def test_wheel_event_ignored(self):
        """Wheel events are ignored and do not change the value."""
        spin = SpinBox()
        spin.setRange(0, 100)
        spin.setValue(50)

        event = _make_wheel_event(delta=120)
        spin.wheelEvent(event)

        assert spin.value() == 50
        assert event.isAccepted() is False

    def test_wheel_event_negative_delta_ignored(self):
        """Wheel events with negative delta are also ignored."""
        spin = SpinBox()
        spin.setRange(0, 100)
        spin.setValue(50)

        event = _make_wheel_event(delta=-120)
        spin.wheelEvent(event)

        assert spin.value() == 50

    def test_set_value_works_normally(self):
        """setValue still works as expected (wheel is blocked, not setValue)."""
        spin = SpinBox()
        spin.setRange(0, 100)
        spin.setValue(42)
        assert spin.value() == 42


# ---------------------------------------------------------------------------
# DoubleSpinBox (floating point)
# ---------------------------------------------------------------------------


class TestDoubleSpinBox:
    """Tests for the custom DoubleSpinBox (QDoubleSpinBox subclass)."""

    def test_instantiation(self):
        """DoubleSpinBox can be created without arguments."""
        spin = DoubleSpinBox()
        assert spin is not None

    def test_is_qdoublespinbox(self):
        """DoubleSpinBox is a subclass of QDoubleSpinBox."""
        from PySide6.QtWidgets import QDoubleSpinBox

        spin = DoubleSpinBox()
        assert isinstance(spin, QDoubleSpinBox)

    def test_focus_policy_is_strong_focus(self):
        """DoubleSpinBox sets focus policy to StrongFocus on init."""
        spin = DoubleSpinBox()
        assert spin.focusPolicy() == Qt.FocusPolicy.StrongFocus

    def test_wheel_event_ignored(self):
        """Wheel events are ignored and do not change the value."""
        spin = DoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setValue(50.0)

        event = _make_wheel_event(delta=120)
        spin.wheelEvent(event)

        assert spin.value() == pytest.approx(50.0)
        assert event.isAccepted() is False

    def test_wheel_event_negative_delta_ignored(self):
        """Wheel events with negative delta are also ignored."""
        spin = DoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setValue(50.0)

        event = _make_wheel_event(delta=-120)
        spin.wheelEvent(event)

        assert spin.value() == pytest.approx(50.0)

    def test_set_value_works_normally(self):
        """setValue still works as expected."""
        spin = DoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setValue(3.14)
        assert spin.value() == pytest.approx(3.14)


# ---------------------------------------------------------------------------
# normalize_proportion_spinboxes
# ---------------------------------------------------------------------------


class TestNormalizeProportionSpinboxes:
    """Tests for normalize_proportion_spinboxes()."""

    @staticmethod
    def _make_spinboxes(values: list[float]) -> list[DoubleSpinBox]:
        """Helper: create DoubleSpinBox instances with given values."""
        spinboxes = []
        for v in values:
            spin = DoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setDecimals(2)
            spin.setValue(v)
            spinboxes.append(spin)
        return spinboxes

    def test_equal_values_normalize_to_equal_shares(self):
        """Three equal values normalize to ~0.33, 0.33, 0.34 (sum=1.0)."""
        spins = self._make_spinboxes([1.0, 1.0, 1.0])
        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        assert sum(result) == pytest.approx(1.0)
        # Each should be roughly 1/3
        for v in result:
            assert 0.3 <= v <= 0.34

    def test_unequal_values_sum_to_one(self):
        """Unequal values are normalized proportionally and sum to 1.0."""
        spins = self._make_spinboxes([0.5, 0.3, 0.2])
        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        assert sum(result) == pytest.approx(1.0)
        # Proportions should be maintained (0.5 > 0.3 > 0.2)
        assert result[0] >= result[1] >= result[2]

    def test_already_summing_to_one(self):
        """Values already summing to 1.0 are unchanged."""
        spins = self._make_spinboxes([0.5, 0.3, 0.2])
        normalize_proportion_spinboxes(spins)

        assert spins[0].value() == pytest.approx(0.5)
        assert spins[1].value() == pytest.approx(0.3)
        assert spins[2].value() == pytest.approx(0.2)

    def test_single_spinbox_normalizes_to_one(self):
        """A single spinbox with a positive value normalizes to 1.0."""
        spins = self._make_spinboxes([0.7])
        normalize_proportion_spinboxes(spins)

        assert spins[0].value() == pytest.approx(1.0)

    def test_two_spinboxes_sum_to_one(self):
        """Two spinboxes normalize proportionally and sum to 1.0."""
        spins = self._make_spinboxes([0.3, 0.7])
        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        assert sum(result) == pytest.approx(1.0)
        assert result[0] == pytest.approx(0.3)
        assert result[1] == pytest.approx(0.7)

    def test_all_zeros_unchanged(self):
        """When all values are zero (total=0), values are not changed."""
        spins = self._make_spinboxes([0.0, 0.0, 0.0])
        normalize_proportion_spinboxes(spins)

        for s in spins:
            assert s.value() == pytest.approx(0.0)

    def test_large_values_normalize_correctly(self):
        """Large values (>1) are still normalized to sum to 1.0."""
        spins = self._make_spinboxes([0.0, 0.0, 0.0])
        # Override range to allow larger values for this test
        for s in spins:
            s.setRange(0.0, 100.0)
        spins[0].setValue(10.0)
        spins[1].setValue(20.0)
        spins[2].setValue(70.0)

        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        assert sum(result) == pytest.approx(1.0)
        assert result[0] == pytest.approx(0.10)
        assert result[1] == pytest.approx(0.20)
        assert result[2] == pytest.approx(0.70)

    def test_diff_correction_applied_to_last(self):
        """Rounding remainder is applied to the last spinbox to ensure sum=1.0 exactly."""
        # Use values that produce rounding drift
        spins = self._make_spinboxes([0.0, 0.0, 0.0])
        for s in spins:
            s.setRange(0.0, 100.0)
        spins[0].setValue(1.0)
        spins[1].setValue(1.0)
        spins[2].setValue(1.0)

        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        # The sum must be exactly 1.0 (the diff correction ensures this)
        assert sum(result) == pytest.approx(1.0, abs=1e-10)

    def test_one_zero_among_positives(self):
        """A zero among positive values stays zero after normalization."""
        spins = self._make_spinboxes([0.0, 0.5, 0.5])
        normalize_proportion_spinboxes(spins)

        assert spins[0].value() == pytest.approx(0.0)
        assert sum(s.value() for s in spins) == pytest.approx(1.0)

    def test_many_spinboxes_sum_to_one(self):
        """Five spinboxes with varied values still sum to 1.0."""
        spins = self._make_spinboxes([0.0] * 5)
        for s in spins:
            s.setRange(0.0, 100.0)
        for i, v in enumerate([10, 20, 30, 15, 25]):
            spins[i].setValue(float(v))

        normalize_proportion_spinboxes(spins)

        result = [s.value() for s in spins]
        assert sum(result) == pytest.approx(1.0)
