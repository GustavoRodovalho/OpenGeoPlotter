from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import RectangleSelector
from matplotlib.figure import Figure
import matplotlib.patches as patches
import pandas as pd

class LocalizationMap(FigureCanvas):
    def __init__(self, df, selected_columns, parent_layout, point_list):
        self.df = df
        self.selected_columns = selected_columns
        self.point_list = point_list  # List widget connected to the map widget
        self.mode = "Latitude/Longitude"
        self.selector = None
        self.rectangles = []  # store drawn rectangles

        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)

        super(LocalizationMap, self).__init__(self.fig)
        parent_layout.addWidget(self)

        # connect right-click event
        self.mpl_connect("button_press_event", self.on_mouse_click)

    def plot_localization(self, mode):
        self.mode = mode
        self.ax.clear()
        self.rectangles.clear()  # clear stored rectangles

        if mode == "Latitude/Longitude":
            x_key = "Longitude"
            y_key = "Latitude"
            self.ax.set_xlabel("Longitude")
            self.ax.set_ylabel("Latitude")
        else:
            x_key = "X"
            y_key = "Y"
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")

        # Get coordinates
        x = pd.to_numeric(self.df[self.selected_columns.get(x_key)].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        y = pd.to_numeric(self.df[self.selected_columns.get(y_key)].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        valid = x.notna() & y.notna()
        self.x = x[valid]
        self.y = y[valid]
        self.valid_indices = self.df.index[valid]

        if x is None or y is None or len(x) == 0 or len(y) == 0:
            self.ax.text(0.5, 0.5, "Coordinates not specified",
                         ha='center', va='center', fontsize=14, color='k',
                         transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        else:
            self.ax.scatter(self.x, self.y, c='blue', edgecolors='k', marker='o', zorder=3)
            self.ax.grid(True, zorder=0)
            x_margin = (x.max() - x.min()) * 0.05
            y_margin = (y.max() - y.min()) * 0.05
            self.ax.set_xlim(x.min() - x_margin, x.max() + x_margin)
            self.ax.set_ylim(y.min() - y_margin, y.max() + y_margin)

        # Enable rectangle selector
        if self.selector:
            self.selector.disconnect_events()
        self.selector = RectangleSelector(
            self.ax,
            self.on_select,
            useblit=True,
            button=[1],  # left mouse button only
            minspanx=0, minspany=0,
            spancoords='data',
            interactive=False
        )
        self.selector.set_active(True)
        self.draw()

    def on_select(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        if None in (x1, y1, x2, y2):
            return

        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        # draw persistent rectangle
        rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                 linewidth=1.5, edgecolor='red', facecolor='none', alpha=0.7)
        self.ax.add_patch(rect)
        self.rectangles.append(rect)

        x_key = self.selected_columns.get("Longitude") if self.mode == "Latitude/Longitude" else self.selected_columns.get("X")
        y_key = self.selected_columns.get("Latitude") if self.mode == "Latitude/Longitude" else self.selected_columns.get("Y")
        well_key = self.selected_columns.get("Well ID")

        if well_key and x_key in self.df.columns and y_key in self.df.columns:
            mask = (
                (self.x.to_numpy() >= xmin) & (self.x.to_numpy() <= xmax) &
                (self.y.to_numpy() >= ymin) & (self.y.to_numpy() <= ymax)
            )
            selected_indices = self.valid_indices[mask]
            selected = self.df.loc[selected_indices]
            wells = selected[well_key].dropna().unique()

            if len(wells) > 0:
                current_wells = {self.point_list.item(i).text() for i in range(self.point_list.count())}
                for well in wells:
                    if str(well) not in current_wells:
                        self.point_list.addItem(str(well))

        self.draw()

    def on_mouse_click(self, event):
        # right-click clears rectangles and list
        if event.button == 3:  # right mouse button
            # remove all drawn rectangles
            for rect in self.rectangles:
                rect.remove()
            self.rectangles.clear()

            # clear list widget
            self.point_list.clear()

            self.draw()