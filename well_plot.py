from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QDialog, QPushButton, QLabel, QListWidget, QGroupBox, 
    QComboBox, QFormLayout, QSpinBox, QLineEdit, QDialogButtonBox,
    QListWidgetItem, QColorDialog, QMessageBox, QCheckBox
)
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotConfigDialog(QDialog):
    # QDialog with Tabs
    def __init__(self, df, remaining_columns, parent=None):
        super().__init__(parent)
        self.df = df
        self.remaining_columns = remaining_columns
        self.setWindowTitle("Add Plots")
        self.resize(600, 400)

        # Tab widget
        self.tabs = QTabWidget()
        self.curve_tab = CurvePlotTab(self.df, remaining_columns)
        self.time_tab = TimeSeriesPlotTab(self.df, remaining_columns)
        self.prop_tab = ProportionPlotTab(self.df, remaining_columns)
        self.litho_tab = LithologyPlotTab(self.df, remaining_columns)

        self.tabs.addTab(self.curve_tab, "Curve Plot")
        self.tabs.addTab(self.time_tab, "Time Series Plot")
        self.tabs.addTab(self.prop_tab, "Proportion Plot")
        self.tabs.addTab(self.litho_tab, "Lithology Plot")

        # Dialog buttons (OK / Cancel)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_parameters(self):
        """Return all configured parameters as a dict."""
        return {
            "curve": self.curve_tab.get_parameters(),
            "time": self.time_tab.get_parameters(),
            "proportion": self.prop_tab.get_parameters(),
            "lithology": self.litho_tab.get_parameters(),
        }

# Individual Tabs
class CurvePlotTab(QWidget):
    def __init__(self, df, remaining_columns):
        super().__init__()
        self.df = df
        self.remaining_columns = remaining_columns
        self.curves = [] # will store dicts for each selected variable

        layout = QVBoxLayout()
        form = QFormLayout()

        # Variable to plot
        self.var_combo = QComboBox()
        self.var_combo.addItems(remaining_columns)
        form.addRow("Variable:", self.var_combo)
        # Curve Name
        self.curve_name = QLineEdit()
        form.addRow("Curve Name:", self.curve_name)
        # Curve Color (clickable button)
        color_layout = QHBoxLayout()
        self.color_display = QLineEdit()
        self.color_display.setText("")
        self.color_display.setReadOnly(True)
        color_button = QPushButton("Select Color")
        color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(color_button)
        form.addRow("Curve Color:", color_layout)
        # Unit
        self.unit_edit = QLineEdit()
        form.addRow("Unit:", self.unit_edit)

        add_btn = QPushButton("Add Curve")
        add_btn.clicked.connect(self.add_curve)
        form.addRow(add_btn)

        layout.addLayout(form)

        layout.addWidget(QLabel("Added Curves:"))
        self.curve_list = QListWidget()
        layout.addWidget(self.curve_list)
        remove_btn = QPushButton("Remove Selected Curves")
        remove_btn.clicked.connect(self.remove_selected_curves)
        layout.addWidget(remove_btn)

        self.setLayout(layout)

    def choose_color(self):
        color = QColorDialog.getColor(QColor("blue"), self, "Select Curve Color")
        if color.isValid():
            self.color_display.setText(color.name())
            self.color_display.setStyleSheet(f"background-color: {color.name()};")

    def add_curve(self):
        var = self.var_combo.currentText()
        name = self.curve_name.text().strip() or var
        color = self.color_display.text().strip()
        unit = self.unit_edit.text().strip()

        # basic validation
        if not var or not color:
            QMessageBox.warning(self, "Incomplete Input", "Please select a variable and color.")
            return

        curve_info = {
            "variable": var,
            "name": name,
            "color": color,
            "unit": unit
        }
        self.curves.append(curve_info)

        # show in list
        item = QListWidgetItem(f"{name} ({var}) - {color} [{unit}]")
        self.curve_list.addItem(item)

        # optional: clear text fields for new entry
        self.curve_name.clear()
        self.unit_edit.clear()

    def remove_selected_curves(self):
        selected = self.curve_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a curve to remove.")
            return
        for item in selected:
            idx = self.curve_list.row(item)
            self.curve_list.takeItem(idx)
            self.curves.pop(idx)

    def get_curves(self):
        """Return all configured curve info."""
        return self.curves

    def get_parameters(self):
        return {
            "variable": self.var_combo.currentText(),
            "depth": self.depth_col.currentText(),
            "color": self.line_color.text()
        }

class TimeSeriesPlotTab(QWidget):
    def __init__(self, df, remaining_columns):
        super().__init__()
        self.df = df
        self.remaining_columns = remaining_columns
        self.series = [] # list of dicts with {"start_col", "end_col", "name", "colormap", "logscale", "unit"}

        layout = QVBoxLayout()
        form = QFormLayout()

        # Select range of columns
        range_layout = QHBoxLayout()
        self.start_combo = QComboBox()
        self.start_combo.addItems(remaining_columns)
        self.end_combo = QComboBox()
        self.end_combo.addItems(remaining_columns)
        range_layout.addWidget(self.start_combo)
        range_layout.addWidget(QLabel("to"))
        range_layout.addWidget(self.end_combo)
        form.addRow("Columns Range:", range_layout)
        # Series name
        self.series_name = QLineEdit()
        form.addRow("Series Name:", self.series_name)
        # Selection of some of the most common matplotlib colormaps
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(sorted(["viridis", "plasma", "inferno", "magma", "cividis", "jet", "turbo", "coolwarm", "Greys", "Spectral"]))
        form.addRow("Colormap:", self.colormap_combo)
        # Log scale option
        self.log_checkbox = QCheckBox("Use logarithmic scale for bins")
        form.addRow(self.log_checkbox)
        # Unit name
        self.unit_edit = QLineEdit()
        form.addRow("Unit:", self.unit_edit)

        add_btn = QPushButton("Add Time Series")
        add_btn.clicked.connect(self.add_series)
        form.addRow(add_btn)

        layout.addLayout(form)

        layout.addWidget(QLabel("Added Time Series:"))
        self.series_list = QListWidget()
        layout.addWidget(self.series_list)
        remove_btn = QPushButton("Remove Selected Series")
        remove_btn.clicked.connect(self.remove_selected_series)
        layout.addWidget(remove_btn)

        self.setLayout(layout)

    def add_series(self):
        start_col = self.start_combo.currentText()
        end_col = self.end_combo.currentText()
        name = self.series_name.text().strip() or f"{start_col}-{end_col}"
        cmap = self.colormap_combo.currentText()
        logscale = self.log_checkbox.isChecked()
        unit = self.unit_edit.text().strip()

        # Get indices to ensure valid range
        start_idx = self.remaining_columns.index(start_col)
        end_idx = self.remaining_columns.index(end_col)
        if start_idx > end_idx:
            QMessageBox.warning(self, "Invalid Range", "The start column must come before the end column.")
            return

        # Prevent duplicates
        for s in self.series:
            if s["start_col"] == start_col and s["end_col"] == end_col:
                QMessageBox.warning(self, "Duplicate Range", "This range has already been added.")
                return

        series_info = {
            "start_col": start_col,
            "end_col": end_col,
            "name": name,
            "colormap": cmap,
            "logscale": logscale,
            "unit": unit
        }
        self.series.append(series_info)

        self.series_list.addItem(
            QListWidgetItem(f"{name}: {start_col} → {end_col} | cmap={cmap}, log={logscale}, unit={unit}")
        )

        # Reset name/unit fields
        self.series_name.clear()
        self.unit_edit.clear()
        self.log_checkbox.setChecked(False)

    def remove_selected_series(self):
        selected = self.series_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a time series to remove.")
            return
        for item in selected:
            idx = self.series_list.row(item)
            self.series_list.takeItem(idx)
            self.series.pop(idx)

    def get_series(self):
        """Return all configured time series as a list of dicts."""
        return self.series

class ProportionPlotTab(QWidget):
    def __init__(self, df, remaining_columns):
        super().__init__()
        layout = QVBoxLayout()
        form = QFormLayout()
        self.category_var = QComboBox()
        self.category_var.addItems(remaining_columns)
        form.addRow("Categorical variable:", self.category_var)
        layout.addLayout(form)
        self.setLayout(layout)

    def get_parameters(self):
        return {
            "category": self.category_var.currentText()
        }


class LithologyPlotTab(QWidget):
    def __init__(self, df, remaining_columns):
        super().__init__()
        layout = QVBoxLayout()
        form = QFormLayout()
        self.lith_var = QComboBox()
        self.lith_var.addItems(remaining_columns)
        self.pattern = QLineEdit("sandstone, shale, limestone")
        form.addRow("Lithology column:", self.lith_var)
        form.addRow("Patterns:", self.pattern)
        layout.addLayout(form)
        self.setLayout(layout)

    def get_parameters(self):
        return {
            "lithology": self.lith_var.currentText(),
            "patterns": self.pattern.text().split(',')
        }


# Integration into your existing tab
class WellVisualizerTab(QWidget):
    def __init__(self, df, selected_columns):
        super().__init__()
        self.df = df
        self.selected_columns = selected_columns

        sidebar_menu = QVBoxLayout()
        self.add_button = QPushButton("Add Plots")
        sidebar_menu.addWidget(self.add_button)
        self.well_list = QListWidget()
        sidebar_menu.addWidget(self.well_list)
        self.remove_selection = QPushButton("Remove selected depths")
        sidebar_menu.addWidget(self.remove_selection)
        sidebar_menu_box = QGroupBox("Plots Settings")
        sidebar_menu_box.setMaximumWidth(200)
        sidebar_menu_box.setLayout(sidebar_menu)

        # Plots layout
        self.plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(5, 5))
        self.plot_canvas = FigureCanvas(self.figure)
        self.plot_layout.addWidget(self.plot_canvas)

        # Assemble layouts
        full_layout = QHBoxLayout()
        full_layout.addWidget(sidebar_menu_box)
        full_layout.addLayout(self.plot_layout)
        self.setLayout(full_layout)

        # Connect "Add Plots" button
        self.add_button.clicked.connect(self.add_plots)

    def add_plots(self):
        remaining_columns = [col for col in self.df.columns if col not in self.selected_columns]
        dialog = PlotConfigDialog(self.df, remaining_columns, self)
        if dialog.exec_() == QDialog.Accepted:
            params = dialog.get_parameters()
            print("User selected parameters:", params)
            # TODO: use params to draw on self.figure
            # Example:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            var = params["curve"]["variable"]
            depth = params["curve"]["depth"]
            ax.plot(self.df[depth], self.df[var], color=params["curve"]["color"])
            self.plot_canvas.draw()


# # Load and clean data
# df = pd.read_csv("data/Dataset_unificado_T2.csv", sep=";", low_memory=False)

# # Convert comma decimals to dots and numeric
# for col in df.columns[1:]:
#     df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
#     df[col] = pd.to_numeric(df[col], errors="coerce")

# # Extract numeric part of the time columns
# time_cols = df.columns[7:37]
# times = time_cols.to_series().str.extract(r'([\d\.eE+-]+)').astype(float)[0].values

# # Select one well (first one)
# well = df['Well Name'].unique()[0]
# well_df = df.loc[df['Well Name'] == well, :]

# # Get depths and corresponding NMR amplitudes
# depths = well_df['TVD'].values
# data = well_df.iloc[:, 7:37].values  # shape = (n_depths, n_times)

# # Sort depths in ascending order (optional, good for visualization)
# sort_idx = np.argsort(depths)
# depths = depths[sort_idx]
# data = data[sort_idx, :]

# # Logs to plot
# log_cols = [
#     "Sonic/DTC",
#     "Resistivity/Deep",
#     "Spectral Gamma Ray/U",
#     "Spectral Gamma Ray/TH",
#     "Spectral Gamma Ray/K (Spec)",
#     "Gamma Ray",
#     "Density",
#     "Photoelectric Factor",
#     "Lithogeochemical/Ca",
#     "Lithogeochemical/Si",
#     "Lithogeochemical/Fe",
#     "Lithogeochemical/Al",
#     "Lithogeochemical/Ti",
#     "Lithogeochemical/S",
#     "Lithogeochemical/FY2W",
#     "Neutron/Thermal Porosity"
# ]

# # Plot as a 2D color map
# n_logs = len(log_cols)
# fig = plt.figure(figsize=(2+n_logs*1.5, 8))
# gs = GridSpec(1, n_logs+1, width_ratios=[3] + [1]*n_logs, wspace=0.1)

# # Time series log
# ax0 = fig.add_subplot(gs[0,0])
# pcm = ax0.pcolormesh(times, depths, data, shading='auto', cmap='viridis')
# ax0.set_xscale('log')
# ax0.set_xlabel('Time (s)')
# ax0.set_ylabel('Depth (m)')
# ax0.invert_yaxis()
# cbar = plt.colorbar(pcm,ax=ax0,pad=0.01)
# cbar.set_label('Amplitude')

# # Well logs
# for i, col in enumerate(log_cols):
#     ax = fig.add_subplot(gs[0, i+1], sharey=ax0)
#     log_data = well_df[col].values[sort_idx]
    
#     ax.plot(log_data, depths, color="black", linewidth=0.8)
#     ax.set_xlabel(col.split("/")[-1], fontsize=6)  # shorter label
#     ax.invert_yaxis()
#     ax.grid(True, linestyle=":", alpha=0.4)
#     ax.set_yticklabels([])  # only leftmost has depth labels
    
#     # Optional: auto limits with small padding
#     finite_data = log_data[np.isfinite(log_data)]
#     if len(finite_data) > 0:
#         xmin, xmax = np.nanpercentile(finite_data, [2, 98])
#         ax.set_xlim(xmin, xmax)
    
#     ax.set_title(col, fontsize=6, pad=4)

# plt.tight_layout()
# plt.show()