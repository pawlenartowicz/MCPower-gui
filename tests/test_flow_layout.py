"""Tests for FlowWidget — flow layout that wraps children left-to-right."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QWidget

from mcpower_gui.widgets.flow_layout import FlowWidget

_app = QApplication.instance() or QApplication([])


@pytest.fixture
def flow():
    widget = FlowWidget(h_spacing=6, v_spacing=6)
    widget.show()
    yield widget
    widget.deleteLater()


def _add_children(parent: FlowWidget, sizes: list[tuple[int, int]]) -> list[QWidget]:
    """Create fixed-size child widgets within the FlowWidget.

    Parameters
    ----------
    parent : FlowWidget
        The parent flow widget.
    sizes : list[tuple[int, int]]
        (width, height) for each child widget.

    Returns
    -------
    list[QWidget]
        The created child widgets.
    """
    children = []
    for w, h in sizes:
        child = QWidget(parent)
        child.setFixedSize(w, h)
        child.show()
        children.append(child)
    return children


# ---------------------------------------------------------------------------
# _layout_children
# ---------------------------------------------------------------------------


class TestLayoutChildren:
    """Tests for _layout_children() — positions children and returns height."""

    def test_empty_children_returns_zero(self, flow):
        """No children produces zero height."""
        height = flow._layout_children(400)
        assert height == 0

    def test_single_child(self, flow):
        """A single child is placed at the origin and height equals its height."""
        children = _add_children(flow, [(50, 30)])
        height = flow._layout_children(400)

        assert height == 30
        assert children[0].x() == 0
        assert children[0].y() == 0

    def test_all_fit_single_row(self, flow):
        """Three children that fit within the width stay on one row."""
        # 3 children each 50px wide: 50 + 6 + 50 + 6 + 50 = 162 total
        children = _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        height = flow._layout_children(200)

        assert height == 30
        # All children on y=0
        for child in children:
            assert child.y() == 0
        # Positions: 0, 56, 112
        assert children[0].x() == 0
        assert children[1].x() == 56  # 50 + 6
        assert children[2].x() == 112  # 50 + 6 + 50 + 6

    def test_wrapping_to_two_rows(self, flow):
        """Children that exceed the width wrap to the next row."""
        # Width 120: first two fit (50 + 6 + 50 = 106 <= 120), third wraps
        children = _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        height = flow._layout_children(120)

        # Two rows: 30 + 6 (v_spacing) + 30 = 66
        assert height == 66
        # First row: children 0 and 1
        assert children[0].y() == 0
        assert children[1].y() == 0
        # Second row: child 2
        assert children[2].y() == 36  # 30 + 6
        assert children[2].x() == 0

    def test_wrapping_to_three_rows(self, flow):
        """Children wrap across three rows when width is very narrow."""
        # Width 55: only one child per row (each child is 50px wide)
        children = _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        height = flow._layout_children(55)

        # Three rows: 30 + 6 + 30 + 6 + 30 = 102
        assert height == 102
        assert children[0].y() == 0
        assert children[1].y() == 36
        assert children[2].y() == 72

    def test_mixed_heights_uses_tallest_in_row(self, flow):
        """Row height is determined by the tallest child in that row."""
        # Width 120: child0 (50x20) and child1 (50x40) fit on row 1,
        # child2 (50x25) wraps to row 2
        children = _add_children(flow, [(50, 20), (50, 40), (50, 25)])
        height = flow._layout_children(120)

        # Row 1 height: max(20, 40) = 40
        # Row 2 height: 25
        # Total: 40 + 6 + 25 = 71
        assert height == 71
        assert children[0].y() == 0
        assert children[1].y() == 0
        assert children[2].y() == 46  # 40 + 6

    def test_child_exactly_fits_width(self, flow):
        """A child whose right edge equals the width stays on the current row."""
        # One child exactly 100px wide in a 100px container
        children = _add_children(flow, [(100, 30)])
        height = flow._layout_children(100)

        assert height == 30
        assert children[0].x() == 0
        assert children[0].y() == 0

    def test_children_resized_to_size_hint(self, flow):
        """Children are resized to their sizeHint (i.e., fixedSize) by layout."""
        children = _add_children(flow, [(80, 25)])
        flow._layout_children(400)

        assert children[0].width() == 80
        assert children[0].height() == 25

    def test_hidden_children_are_skipped(self, flow):
        """Hidden children are excluded from layout calculations."""
        children = _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        children[1].hide()

        height = flow._layout_children(400)

        # Only two visible children: height is one row of 30
        assert height == 30
        # The visible children should be at x=0 and x=56
        assert children[0].x() == 0
        assert children[2].x() == 56

    def test_different_widths(self, flow):
        """Children with varying widths are positioned correctly."""
        children = _add_children(flow, [(30, 25), (70, 25), (40, 25)])
        height = flow._layout_children(200)

        assert height == 25
        assert children[0].x() == 0
        assert children[1].x() == 36  # 30 + 6
        assert children[2].x() == 112  # 30 + 6 + 70 + 6

    def test_custom_spacing(self):
        """Non-default h_spacing and v_spacing are respected."""
        flow = FlowWidget(h_spacing=10, v_spacing=20)
        flow.show()
        children = _add_children(flow, [(50, 30), (50, 30), (50, 30)])

        # Width 120: 50 + 10 + 50 = 110 fits, but 110 + 50 = 160 > 120
        height = flow._layout_children(120)

        # Two rows: 30 + 20 + 30 = 80
        assert height == 80
        assert children[0].x() == 0
        assert children[1].x() == 60  # 50 + 10
        assert children[2].x() == 0
        assert children[2].y() == 50  # 30 + 20

        flow.deleteLater()


# ---------------------------------------------------------------------------
# _layout_children_dry
# ---------------------------------------------------------------------------


class TestLayoutChildrenDry:
    """Tests for _layout_children_dry() — height calculation without moving."""

    def test_empty_children_returns_zero(self, flow):
        """No children produces zero height."""
        height = flow._layout_children_dry(400)
        assert height == 0

    def test_single_child(self, flow):
        """A single child returns its height."""
        _add_children(flow, [(50, 30)])
        height = flow._layout_children_dry(400)
        assert height == 30

    def test_single_row_height(self, flow):
        """All children on one row — height equals tallest child."""
        _add_children(flow, [(50, 25), (50, 35), (50, 30)])
        height = flow._layout_children_dry(400)
        assert height == 35

    def test_wrapping_height(self, flow):
        """Wrapping children produce the same height as _layout_children."""
        _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        height = flow._layout_children_dry(120)
        # Two rows: 30 + 6 + 30 = 66
        assert height == 66

    def test_matches_layout_children_single_row(self, flow):
        """Dry-run height matches actual layout height (single row)."""
        _add_children(flow, [(40, 20), (60, 25), (30, 20)])
        actual = flow._layout_children(400)
        dry = flow._layout_children_dry(400)
        assert dry == actual

    def test_matches_layout_children_multi_row(self, flow):
        """Dry-run height matches actual layout height (multiple rows)."""
        _add_children(flow, [(50, 30), (50, 30), (50, 30), (50, 30)])
        actual = flow._layout_children(120)
        dry = flow._layout_children_dry(120)
        assert dry == actual

    def test_does_not_move_children(self, flow):
        """Dry-run does not change child positions."""
        children = _add_children(flow, [(50, 30), (50, 30)])
        # Record original positions
        original_positions = [(c.x(), c.y()) for c in children]

        flow._layout_children_dry(120)

        # Positions must remain unchanged
        for child, (ox, oy) in zip(children, original_positions):
            assert child.x() == ox
            assert child.y() == oy

    def test_hidden_children_are_skipped(self, flow):
        """Hidden children are excluded from dry-run height."""
        children = _add_children(flow, [(50, 30), (50, 40), (50, 30)])
        children[1].hide()

        height = flow._layout_children_dry(400)
        # Only children[0] (30px) and children[2] (30px) visible, single row
        assert height == 30

    def test_matches_layout_children_mixed_heights(self, flow):
        """Dry-run matches actual layout for mixed-height children across rows."""
        _add_children(flow, [(50, 20), (50, 40), (50, 25)])
        actual = flow._layout_children(120)
        dry = flow._layout_children_dry(120)
        assert dry == actual


# ---------------------------------------------------------------------------
# sizeHint
# ---------------------------------------------------------------------------


class TestSizeHint:
    """Tests for sizeHint() — returns QSize with calculated height."""

    def test_empty_returns_zero_height(self, flow):
        """No children: sizeHint height is 0."""
        hint = flow.sizeHint()
        assert hint.height() == 0

    def test_returns_qsize(self, flow):
        """sizeHint returns a QSize instance."""
        hint = flow.sizeHint()
        assert isinstance(hint, QSize)

    def test_height_matches_dry_layout(self, flow):
        """sizeHint height equals _layout_children_dry for the same width."""
        _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        flow.resize(200, 100)

        hint = flow.sizeHint()
        expected_h = flow._layout_children_dry(200)
        assert hint.height() == expected_h

    def test_width_matches_widget_width(self, flow):
        """sizeHint width equals the widget's current width."""
        flow.resize(300, 100)
        _add_children(flow, [(50, 30)])

        hint = flow.sizeHint()
        assert hint.width() == 300

    def test_default_width_when_zero(self, flow):
        """When widget width is 0, sizeHint uses fallback width of 400."""
        _add_children(flow, [(50, 30)])
        # Fresh FlowWidget has 0 width before being shown
        flow.resize(0, 0)

        hint = flow.sizeHint()
        assert hint.width() == 400

    def test_single_row_height(self, flow):
        """sizeHint with children fitting in one row."""
        _add_children(flow, [(50, 30), (50, 30)])
        flow.resize(200, 100)

        hint = flow.sizeHint()
        assert hint.height() == 30

    def test_multi_row_height(self, flow):
        """sizeHint with children wrapping to multiple rows."""
        _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        flow.resize(120, 100)

        hint = flow.sizeHint()
        # Two rows: 30 + 6 + 30 = 66
        assert hint.height() == 66

    def test_height_never_negative(self, flow):
        """sizeHint height is never negative, even with no children."""
        hint = flow.sizeHint()
        assert hint.height() >= 0


# ---------------------------------------------------------------------------
# reflow
# ---------------------------------------------------------------------------


class TestReflow:
    """Tests for reflow() — positions children and sets fixed height."""

    def test_sets_fixed_height(self, flow):
        """reflow sets the widget's fixed height based on children."""
        _add_children(flow, [(50, 30), (50, 30)])
        flow.resize(200, 100)

        flow.reflow()

        assert flow.height() == 30

    def test_sets_fixed_height_multi_row(self, flow):
        """reflow sets height correctly for multi-row layout."""
        _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        flow.resize(120, 100)

        flow.reflow()

        # Two rows: 30 + 6 + 30 = 66
        assert flow.height() == 66

    def test_empty_children_height_zero(self, flow):
        """reflow with no children sets height to 0."""
        flow.resize(200, 100)
        flow.reflow()
        assert flow.height() == 0

    def test_children_are_positioned(self, flow):
        """reflow positions children (delegates to _layout_children)."""
        children = _add_children(flow, [(50, 30), (50, 30)])
        flow.resize(200, 100)

        flow.reflow()

        assert children[0].x() == 0
        assert children[0].y() == 0
        assert children[1].x() == 56  # 50 + 6

    def test_uses_fallback_width_when_zero(self, flow):
        """reflow uses width=400 when widget width is 0."""
        # 8 children x 50px = 400px + 7 spacings = 442, so wrapping happens
        _add_children(flow, [(50, 30)] * 8)
        flow.resize(0, 0)

        flow.reflow()

        # With width=400, 7 children fit: 7*(50+6) - 6 = 386 <= 400
        # 8th wraps: height = 30 + 6 + 30 = 66
        assert flow.height() == 66

    def test_height_never_negative(self, flow):
        """reflow never produces a negative height."""
        flow.resize(200, 100)
        flow.reflow()
        assert flow.height() >= 0

    def test_reflow_updates_after_child_added(self, flow):
        """Calling reflow after adding new children recalculates height."""
        _add_children(flow, [(50, 30)])
        flow.resize(200, 100)
        flow.reflow()
        assert flow.height() == 30

        # Add more children that cause wrapping
        _add_children(flow, [(50, 30), (50, 30), (50, 30)])
        flow.reflow()
        # 4 children x (50+6) = 224, exceeds 200: wrapping occurs
        # Row 1: 3 children fit: 3*(50+6)-6 = 162 <= 200, 4th child: 162+50 = 212 > 200
        # Actually: child0=0-50, child1=56-106, child2=112-162, child3=168-218 > 200
        # So 3 fit, 4th wraps: height = 30 + 6 + 30 = 66
        assert flow.height() == 66
