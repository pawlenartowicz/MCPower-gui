"""PyQtGraph line plot: power vs sample size with achievement markers."""

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

# Distinguishable colors for up to 10 lines
_COLORS = [
    "#2196F3",
    "#4CAF50",
    "#FF9800",
    "#9C27B0",
    "#F44336",
    "#00BCD4",
    "#795548",
    "#607D8B",
    "#E91E63",
    "#CDDC39",
]


class PowerCurvePlot(QWidget):
    """Multi-line plot of power curves with markers at first-achieved N."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot = pg.PlotWidget(title="Power vs Sample Size")
        self._plot.setBackground("w")
        self._plot.showGrid(x=True, y=True)
        self._plot.setLabel("bottom", "Sample Size")
        self._plot.setLabel("left", "Power (%)")
        self._plot.addLegend()
        layout.addWidget(self._plot)

    def update_plot(
        self,
        sample_sizes: list[int],
        powers_by_test: dict[str, list[float]],
        first_achieved: dict[str, int | None],
        target_power: float,
    ):
        """Redraw with new sample-size search results."""
        self._plot.clear()
        if not sample_sizes or not powers_by_test:
            return

        xs = np.array(sample_sizes)

        for i, (test_name, powers) in enumerate(powers_by_test.items()):
            color = _COLORS[i % len(_COLORS)]
            pen = pg.mkPen(color, width=2)
            self._plot.plot(xs, np.array(powers), pen=pen, name=test_name)

            # Achievement marker
            achieved_n = first_achieved.get(test_name)
            if achieved_n is not None and achieved_n in sample_sizes:
                idx = sample_sizes.index(achieved_n)
                self._plot.plot(
                    [achieved_n],
                    [powers[idx]],
                    pen=None,
                    symbol="o",
                    symbolSize=10,
                    symbolBrush=color,
                )

        # Target power horizontal line
        self._plot.addItem(
            pg.InfiniteLine(
                pos=target_power,
                angle=0,
                pen=pg.mkPen("r", width=2, style=pg.QtCore.Qt.PenStyle.DashLine),
                label=f"Target: {target_power}%",
                labelOpts={"position": 0.9, "color": "r"},
            )
        )

        max_n = max(sample_sizes) if sample_sizes else 100
        self._plot.setYRange(0, 105)
        self._plot.setXRange(0, max_n * 1.05)

        # Bound zoom/pan
        self._plot.setLimits(xMin=0, xMax=max_n * 1.05, yMin=0, yMax=105)
