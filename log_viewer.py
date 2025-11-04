from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QListWidget, QGroupBox, QScrollArea, QSplitter, QDialog, QFormLayout,
    QDialogButtonBox
)
import pyqtgraph as pg
import numpy as np

class CurveSelectionDialog(QDialog):
    """Dialog to select a curve (column) from a pandas DataFrame."""
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Curve")
        self.df = df
        self.selected_column = None

        layout = QFormLayout(self)
        self.curve_combo = QComboBox()
        self.curve_combo.addItems(self.df.columns)
        layout.addRow("Curve:", self.curve_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selection(self):
        if self.exec_() == QDialog.Accepted:
            return self.curve_combo.currentText()
        return None

class LogViewer(QWidget):
    """Well log viewer widget (depth track + scrollable tracks)."""
    def __init__(self, parent=None):
        super().__init__(parent)

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
        # self.splitter.addWidget(self.depth_plot)
        self.splitter.addWidget(self.scroll_area)

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)

        # Data setup
        self.tracks = []
        self.depth = np.linspace(0, 3000, 500)
        # self.depth_plot.plot([0] * len(self.depth), self.depth, pen=None)  # Depth axis guide

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
        # track.getViewBox().setYLink(self.depth_plot.getViewBox())

        self.tracks_layout.addWidget(track)
        self.tracks.append(track)

    def clear_tracks(self):
        """Clear all tracks."""
        for track in self.tracks:
            self.tracks_layout.removeWidget(track)
            track.deleteLater()
        self.tracks = []