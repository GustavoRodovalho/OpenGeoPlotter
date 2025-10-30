from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QListWidget, QGroupBox, QScrollArea, QSplitter
)
import pyqtgraph as pg
import numpy as np


class LogViewer(QWidget):
    """Well log viewer widget (depth track + scrollable tracks)."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Depth track
        self.depth_plot = pg.PlotWidget()
        self.depth_plot.setFixedWidth(80)
        self.depth_plot.invertY(True)
        self.depth_plot.hideAxis('bottom')
        self.depth_plot.showAxis('left', True)
        self.depth_plot.setLabel('left', 'Depth (m)')
        self.depth_plot.setMouseEnabled(x=False, y=True)

        # Container for tracks
        self.tracks_container = QWidget()
        self.tracks_layout = QHBoxLayout(self.tracks_container)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(5)

        # Scroll area for horizontal track scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.tracks_container)

        # Splitter: depth sidebar + tracks
        self.splitter = QSplitter()
        self.splitter.addWidget(self.depth_plot)
        self.splitter.addWidget(self.scroll_area)

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)

        # Data setup
        self.tracks = []
        self.depth = np.linspace(0, 3000, 500)
        self.depth_plot.plot([0] * len(self.depth), self.depth, pen=None)  # Depth axis guide

    def add_curve(self):
        """Add a random curve track linked to the depth axis."""
        curve_data = np.random.random(len(self.depth)) * 100
        track = pg.PlotWidget()
        track.plot(curve_data, self.depth, pen='c')
        track.invertY(True)
        track.showGrid(x=True, y=True, alpha=0.3)
        track.setMouseEnabled(x=True, y=True)
        track.setLabel('bottom', f'Curve {len(self.tracks) + 1}')

        # Link Y axis to the depth axis
        track.getViewBox().setYLink(self.depth_plot.getViewBox())

        self.tracks_layout.addWidget(track)
        self.tracks.append(track)
