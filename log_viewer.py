from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QListWidget, QGroupBox, QScrollArea, QSplitter, QDialog, QFormLayout,
    QDialogButtonBox, QAbstractItemView, QTabWidget
)
import pyqtgraph as pg
import numpy as np

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QDialogButtonBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtCore import Qt

class TrackSelectionDialog(QDialog):
    def __init__(self, df, selected_columns, parent=None):
        super().__init__(parent)
        self.df = df
        self.selected_columns = selected_columns
        self.selected_order = []

        self.setWindowTitle("Select Tracks to Add")
        self.resize(420, 520)

        # Layout
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select curves (drag to reorder):"))

        # Curve List
        self.curve_list = QListWidget()
        self.curve_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.curve_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.curve_list.setDefaultDropAction(Qt.MoveAction)

        layout.addWidget(self.curve_list)

        # Initialize list
        self.reset_to_default()

        # Buttons
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.remove_btn = QPushButton("Remove Selected")
        self.reset_btn = QPushButton("Reset to Default")

        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.reset_btn)
        layout.addLayout(button_layout)

        # Connect buttons
        self.select_all_btn.clicked.connect(self.select_all)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.reset_btn.clicked.connect(self.reset_to_default)

        # OK / Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def reset_to_default(self):
        """Reload the curve list from dataframe (excluding identifier columns)."""
        self.curve_list.clear()
        excluded_cols = set(self.selected_columns.values())
        default_curves = [col for col in self.df.columns if col not in excluded_cols]
        self.curve_list.addItems(default_curves)

    def select_all(self):
        for i in range(self.curve_list.count()):
            self.curve_list.item(i).setSelected(True)

    def remove_selected(self):
        """Remove selected items from the list."""
        for item in self.curve_list.selectedItems():
            row = self.curve_list.row(item)
            self.curve_list.takeItem(row)

    def accept(self):
        """Collect selected items in their visual order."""
        items = []
        for i in range(self.curve_list.count()):
            item = self.curve_list.item(i)
            if item.isSelected():
                items.append(item.text())
        self.selected_order = items
        super().accept()

    def get_selected_curves(self):
        return self.selected_order

class LogViewer(QWidget):
    """Well log viewer widget (depth track + scrollable tracks)."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Container for tracks
        self.tracks_layout = QHBoxLayout()
        self.tracks_container = QWidget()
        self.tracks_container.setLayout(self.tracks_layout)

        # Scroll area for horizontal track scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.tracks_container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        # Tracks list
        self.tracks = []
        self.depths = None
        self.selected_regions = []

    def update_tracks(self, depths, df_curves):
        """Add curves for selected tracks and current well"""
        # Clear log viewer
        for track in self.tracks:
            self.tracks_layout.removeWidget(track)
            track.deleteLater()
        self.tracks = []
        self.selected_regions.clear()

        reference_track = None
        self.depths = depths.values.ravel()

        # Create and link all curve tracks
        for curve_name in df_curves.columns:
            track = pg.PlotWidget()
            track.setMinimumWidth(200)
            track.plot(df_curves[curve_name].values.ravel(), depths.values.ravel(), pen='c')
            track.invertY(True)
            track.showGrid(x=True, y=True, alpha=0.3)
            track.setLabel('bottom', curve_name)
    
            if reference_track is None:
                reference_track = track
                track.setLabel('left', 'Depth')
            else:
                track.setYLink(reference_track)

            track.scene().sigMouseClicked.connect(lambda event, tr=track: self.add_selection_region(tr, event))

            self.tracks_layout.addWidget(track)
            self.tracks.append(track)
        
        self.tracks_container.adjustSize()

    def add_selection_region(self, track, event):
        """Add a selection region on the clicked track."""
        if not track.sceneBoundingRect().contains(event.scenePos()):
            return

        # Create a new vertical region
        region = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Horizontal)
        region.setZValue(10)
        region.setRegion([self.depths.min(), self.depths.max()])  # default range
        region.sigRegionChanged.connect(lambda: self.on_region_changed(region))
        track.addItem(region)
        self.selected_regions.append(region)

        print("🟩 New region added. Drag to adjust the depth range.")

    def on_region_changed(self, region):
        """Called whenever a region is resized/moved."""
        y_min, y_max = region.getRegion()
        print(f"📏 Selected depth range: {y_min:.2f} – {y_max:.2f}")