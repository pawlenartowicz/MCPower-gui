"""PyQtGraph bar chart showing power (%) per effect."""

import numpy as np
import pyqtgraph as pg
from pyqtgraph import LabelItem
from PySide6.QtWidgets import QVBoxLayout, QWidget

from mcpower_gui.theme import current_colors

_TAGLINE = "made in MCPower \u2014 simple Monte Carlo power analysis for complex models"


class PowerBarChart(QWidget):
    """Horizontal bar chart of power percentages with a target-power line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot = pg.PlotWidget(title="Power by Tested Variable")
        colors = current_colors()
        self._plot.setBackground(colors["plot_bg"])
        self._plot.showGrid(x=True, y=False)
        self._plot.setLabel("bottom", "Power (%)")
        tagline = LabelItem(_TAGLINE, size="9pt", color="#888888")
        self._plot.plotItem.layout.addItem(tagline, 4, 1)
        layout.addWidget(self._plot)

        self._target_line = None
        self._bar_item = None

    def update_chart(self, powers: dict[str, float], target_power: float):
        """Redraw with new data.

        Parameters
        ----------
        powers : dict
            {effect_name: power_percentage}
        target_power : float
            Target power line (e.g. 80.0).
        """
        self._plot.clear()
        colors = current_colors()
        self._plot.setBackground(colors["plot_bg"])
        for axis_name in ("left", "bottom"):
            axis = self._plot.getAxis(axis_name)
            axis.setPen(colors["plot_fg"])
            axis.setTextPen(colors["plot_fg"])
        if not powers:
            return

        names = list(powers.keys())
        values = np.array([powers[n] for n in names])
        n = len(names)
        y_pos = np.arange(n)

        # Color: green if >= target, orange otherwise
        brushes = [
            pg.mkBrush("g") if v >= target_power else pg.mkBrush("#e67e22")
            for v in values
        ]

        bar = pg.BarGraphItem(x0=0, y=y_pos, height=0.6, width=values, brushes=brushes)
        self._plot.addItem(bar)

        # Target power vertical line
        self._target_line = pg.InfiniteLine(
            pos=target_power,
            angle=90,
            pen=pg.mkPen("r", width=2, style=pg.QtCore.Qt.PenStyle.DashLine),
            label=f"Target: {target_power}%",
            labelOpts={"position": 0.95, "color": "r"},
        )
        self._plot.addItem(self._target_line)

        # Y-axis tick labels
        ticks = [(i, name) for i, name in enumerate(names)]
        self._plot.getAxis("left").setTicks([ticks])
        self._plot.setYRange(-0.5, n - 0.5)
        self._plot.setXRange(0, 105)

        # Bound zoom/pan
        self._plot.setLimits(xMin=0, xMax=105, yMin=-0.5, yMax=n - 0.5)
