from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QListWidget, QGroupBox, QScrollArea, QSplitter, QDialog, QFormLayout,
    QDialogButtonBox, QAbstractItemView, QTabWidget, QAction
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

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

        # Parameters
        self.tracks = [] # variables
        self.depths = None # depths
        self.selected_regions = [] # regions
        self.well_regions = {} # {well_name: [{"track_index": ..., "y_min": ..., , "y_max": ...}, {}, ...]}

    def update_tracks(self, well_name, depths, df_curves):
        """Add curves for selected tracks and current well"""
        self.well_name = well_name
        self.well_regions.setdefault(well_name, [])
        # Clear log viewer
        for track in self.tracks:
            self.tracks_layout.removeWidget(track)
            track.deleteLater()
        self.tracks.clear()
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

            # Replace ViewBox's context menu handler
            track.plotItem.vb.mouseClickEvent = lambda ev, tr=track: self.handle_viewbox_click(tr, ev)

            track.scene().sigMouseClicked.connect(lambda event, tr=track: self.handle_mouse_click(tr, event))

            self.tracks_layout.addWidget(track)
            self.tracks.append(track)
        
        self.tracks_container.adjustSize()
        # Restore saved regions if any
        self.restore_regions_for_well(well_name)

    def handle_viewbox_click(self, track, ev):
        """Intercept right-click to extend context menu with region removal option."""
        if ev.button() == Qt.RightButton:
            menu = track.plotItem.vb.getMenu(ev)
            view_pos = track.plotItem.vb.mapSceneToView(ev.scenePos())
            clicked_depth = view_pos.y()

            # Clean any previous custom items first
            for action in menu.actions():
                if action.text() == "Remove Selected Region":
                    menu.removeAction(action)
            for action in menu.actions():
                if action.isSeparator():
                    # remove stray separators left from previous call
                    menu.removeAction(action)

            # Detect where the click is (which region)
            clicked_region = None
            for (t, region) in self.selected_regions:
                if t == track:
                    y_min, y_max = region.getRegion()
                    if y_min <= clicked_depth <= y_max:
                        clicked_region = region
                        break

            # Add custom option if above a region
            if clicked_region is not None:
                menu.addSeparator()
                remove_action = QAction("Remove Selected Region", menu)
                remove_action.triggered.connect(lambda _, tr=track, reg=clicked_region: self.remove_region(tr, reg))
                menu.addAction(remove_action)

            menu.popup(ev.screenPos().toPoint())
        else:
            pg.ViewBox.mouseClickEvent(track.plotItem.vb, ev)  # fallback to default behavior

    def handle_mouse_click(self, track, event):
        """Handle left-click (add) and double-click (remove by clicking region)."""
        if not track.sceneBoundingRect().contains(event.scenePos()):
            return

        # Add new selection region on left click
        if event.button() == Qt.LeftButton and not event.double():
            self.add_selection_region(track, event)
            # Append region to 

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
        self.selected_regions.append((track, region))
        self.update_region_list()
        # print("🟩 New region added. Drag to adjust the depth range.")

    def remove_region(self, track, region):
        """Remove the specified selection region from the track."""
        if (track, region) in self.selected_regions:
            track.removeItem(region)
            self.selected_regions.remove((track, region))
            self.update_region_list()
            y_min, y_max = region.getRegion()
            # print(f"❌ Region removed (range {y_min:.2f}-{y_max:.2f})")

    def on_region_changed(self, region):
        """Called whenever a region is resized/moved."""
        self.update_region_list()
        y_min, y_max = region.getRegion()
        # print("📏 Selected well:", self.well_name, f"📏 Selected depth range: {y_min:.2f} – {y_max:.2f}")
    
    def update_region_list(self):
        """Update the internal list of selected regions."""
        regions = []
        for (t, region) in self.selected_regions:
            if self.well_name == getattr(self, 'well_name', None):
                y_min, y_max = region.getRegion()
                # Identify the track by index (safer than by name)
                try:
                    track_index = self.tracks.index(t)
                except ValueError:
                    continue
                regions.append({
                    "track_index": track_index,
                    "y_min": round(float(y_min), 2),
                    "y_max": round(float(y_max), 2)
                })
        self.well_regions[self.well_name] = regions

        parent = self.parent()
        while parent is not None and not hasattr(parent, "update_well_depth_list"):
            parent = parent.parent()
        if parent is not None:
            parent.update_well_depth_list()

    def restore_regions_for_well(self, well_name):
        """Recreate saved selection regions for the given well. 
        It doesnt work if the user change the current track list,
        since it stores the index of the track which the selection was made."""
        if well_name not in self.well_regions:
            return
        
        saved_regions = self.well_regions[well_name]
        for reg in saved_regions: # each dict inside the list of regions
            idx = reg.get("track_index", 0)
            if idx < len(self.tracks):
                track = self.tracks[idx]
                y_min, y_max = reg["y_min"], reg["y_max"]

                region = pg.LinearRegionItem(values=(y_min, y_max), orientation=pg.LinearRegionItem.Horizontal)
                region.setZValue(10)
                region.sigRegionChanged.connect(lambda: self.on_region_changed(region))
                track.addItem(region)
                self.selected_regions.append((track, region))

    def reset_viewer(self, clear_all_wells=True):
        """Completely reset the LogViewer visual state."""
        # Remove all track widgets
        for track in self.tracks:
            self.tracks_layout.removeWidget(track)
            track.deleteLater()
        self.tracks.clear()

        # Clear selections
        self.selected_regions.clear()
        self.depths = None
        self.well_name = None

        # Optionally clear stored well regions
        if clear_all_wells:
            self.well_regions.clear()

        # Adjust layout
        self.tracks_container.adjustSize()