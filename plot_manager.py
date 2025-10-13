from PyQt5.QtWidgets import QLabel, QComboBox, QTextEdit
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import RectangleSelector
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

class LocalizationMap:
    def __init__(self, df, selected_columns, parent_layout):
        self.df = df
        self.selected_columns = selected_columns
        self.parent_layout = parent_layout
        self.canvas = None
        self.ax = None
        self.selector = None
        self.id_boxes = {
            "Latitude/Longitude": QTextEdit(),
            "X/Y": QTextEdit()
        }
        for box in self.id_boxes.values():
            box.setReadOnly(True)
            box.setMinimumHeight(120)

    def plot_localization(self, mode):
        self.current_mode = mode
        current_box = self.id_boxes[mode]

        # Clear previous layout
        while self.parent_layout.count():
            widget = self.parent_layout.takeAt(0).widget()
            if widget:
                widget.setParent(None)

        # Determine coordinate columns
        if mode == "Latitude/Longitude":
            x_col = self.selected_columns.get("Longitude")
            y_col = self.selected_columns.get("Latitude")
            x_label, y_label = "Longitude", "Latitude"
        else:
            x_col = self.selected_columns.get("X")
            y_col = self.selected_columns.get("Y")
            x_label, y_label = "X", "Y"

        # Validate columns
        if not x_col or not y_col or x_col not in self.df.columns or y_col not in self.df.columns:
            message = QTextEdit("Coordinates not specified")
            message.setReadOnly(True)
            self.parent_layout.addWidget(message)
            return

        # Clean and convert data
        x = pd.to_numeric(self.df[x_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        y = pd.to_numeric(self.df[y_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        valid = x.notna() & y.notna()
        x = x[valid]
        y = y[valid]

        # Create plot
        fig = Figure(figsize=(8, 6))
        self.ax = fig.add_subplot(111)
        self.ax.scatter(x, y, c='blue', alpha=0.6, edgecolors='k')
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title("Well Localization Map")
        self.ax.grid(True)

        # Set margins
        x_margin = (x.max() - x.min()) * 0.05
        y_margin = (y.max() - y.min()) * 0.05
        self.ax.set_xlim(x.min() - x_margin, x.max() + x_margin)
        self.ax.set_ylim(y.min() - y_margin, y.max() + y_margin)

        # Add canvas and ID box
        self.canvas = FigureCanvas(fig)
        self.parent_layout.addWidget(self.canvas)
        self.parent_layout.addWidget(current_box)

        # Store data for selection
        self.x_data = x
        self.y_data = y
        self.ids = self.df.loc[valid, self.selected_columns.get("Well ID")]

        # Activate selector
        self.selector = RectangleSelector(
            self.ax,
            self.on_select,
            useblit=True,
            button=[1],
            minspanx=5,
            minspany=5,
            spancoords='data',
            interactive=True
        )
        self.canvas.draw()

    def on_select(self, eclick, erelease):
        x_min, x_max = sorted([eclick.xdata, erelease.xdata])
        y_min, y_max = sorted([eclick.ydata, erelease.ydata])

        selected = (
            (self.x_data >= x_min) & (self.x_data <= x_max) &
            (self.y_data >= y_min) & (self.y_data <= y_max)
        )

        selected_ids = self.ids[selected].dropna().unique()
        box = self.id_boxes.get(self.current_mode)
        if len(selected_ids) > 0:
            box.setPlainText("\n".join(map(str, selected_ids)))
        else:
            box.setPlainText("No wells selected")