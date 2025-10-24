from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QDialog, QPushButton, QLabel, QListWidget, QGroupBox, 
    QComboBox, QFormLayout, QSpinBox, QLineEdit, QDialogButtonBox,
    QListWidgetItem, QColorDialog, QMessageBox, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Plot Configuration Dialog with Tabs
class PlotConfigDialog(QDialog):
    # QDialog with Tabs
    def __init__(self, df, remaining_columns, parent=None):
        super().__init__(parent)
        self.df = df
        self.remaining_columns = remaining_columns
        self.setWindowTitle("Add Plots")
        self.resize(600, 600)

        # Tab widget
        self.tabs = QTabWidget()
        self.curve_tab = CurvePlotTab(self.df, remaining_columns)
        self.time_tab = TimeSeriesPlotTab(self.df, remaining_columns)
        self.prop_tab = ProportionPlotTab(self.df, remaining_columns)

        self.tabs.addTab(self.curve_tab, "Curve Plot")
        self.tabs.addTab(self.time_tab, "Time Series Plot")
        self.tabs.addTab(self.prop_tab, "Proportion Plot")

        # Dialog buttons (OK / Cancel)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)

        # Store plots configs
        self.curves = None
        self.series = None
        self.proportions = None

    def accept(self):
        """Called when user clicks OK. Save results from each tab."""
        try:
            self.curves = self.curve_tab.get_curves()
            self.series = self.time_tab.get_series()
            self.proportions = self.prop_tab.get_proportions()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read plot configurations:\n{e}")
            return  # Do not close dialog if something failed
    
        super().accept()

    def get_parameters(self):
        """Return all configured parameters as a dict."""
        return {
            "curves": self.curve_tab.curves,
            "time series": self.time_tab.series,
            "proportions": self.prop_tab.proportions
        }

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
        self.var_combo.currentTextChanged.connect(self.update_curve_name)
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

    def update_curve_name(self, var_name):
        """Auto-fill the curve name with the selected variable (if user hasn’t typed anything)."""
        # Only overwrite if user hasn’t customized the name
        if not self.curve_name.text().strip():
            self.curve_name.setText(var_name)

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
        self.colormap_combo.addItems(["viridis", "plasma", "inferno", "magma", "cividis", "jet", "turbo", "coolwarm", "Greys", "Spectral"])
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
        self.df = df
        self.remaining_columns = remaining_columns
        self.proportions = []  # list of dicts {"variable_list", "name", "color_list"}
        self.variable_color_pairs = []

        main_layout = QVBoxLayout()
        form = QFormLayout()

        self.plot_name = QLineEdit()
        form.addRow("Proportion Plot Name:", self.plot_name)
        main_layout.addLayout(form)

        # Scroll area for variable/color pairs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        # Add Variable button inside scroll area, after pairs
        self.add_var_btn = QPushButton("Add Variable")
        self.add_var_btn.clicked.connect(self.add_variable_color_pair)
        self.scroll_layout.addWidget(self.add_var_btn)

        # Buttons to manage proportion plots
        add_btn = QPushButton("Add Proportion Plot")
        add_btn.clicked.connect(self.add_proportion_plot)
        self.proportions_list = QListWidget()
        rm_btn = QPushButton("Remove Selected Proportions")
        rm_btn.clicked.connect(self.remove_selected_proportion)
        main_layout.addWidget(add_btn)
        main_layout.addWidget(QLabel("Added Proportions:"))
        main_layout.addWidget(self.proportions_list)
        main_layout.addWidget(rm_btn)
        self.setLayout(main_layout)

        # Add default variable-color row
        if self.remaining_columns:
            self.add_variable_color_pair()

    def add_variable_color_pair(self):
        """Add a new row with (variable combobox + color button + color display + label edit + remove button)."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Variable selector
        variable_box = QComboBox()
        variable_box.addItems(self.remaining_columns)
        # Color choose button
        color_btn = QPushButton("Choose Color")
        color_display = QLabel()
        color_display.setFixedSize(40, 20)
        color_display.setStyleSheet("background-color: #cccccc; border: 1px solid black;")
        # Color dialog
        def choose_color():
            color = QColorDialog.getColor(QColor("blue"), self, "Select Color")
            if color.isValid():
                color_display.setStyleSheet(f"background-color: {color.name()};")
        color_btn.clicked.connect(choose_color)
        # Label for each variable
        label_edit = QLineEdit()
        label_edit.setPlaceholderText("Label")
        label_edit.setFixedWidth(80)
        # Remove variable-color pair
        remove_btn = QPushButton("Remove")

        def remove_row():
            if len(self.variable_color_pairs) <= 1:
                QMessageBox.warning(self, "Cannot Remove", "At least one variable-color pair is required.")
                return
            row_widget.setParent(None)
            if (variable_box, color_display, row_widget) in self.variable_color_pairs:
                self.variable_color_pairs.remove((variable_box, color_display, row_widget))

        remove_btn.clicked.connect(remove_row)

        # Assemble row
        row_layout.addWidget(variable_box)
        row_layout.addWidget(color_btn)
        row_layout.addWidget(color_display)
        row_layout.addWidget(label_edit)
        row_layout.addWidget(remove_btn)

        # Insert rows above the "Add Variable" button
        idx = self.scroll_layout.indexOf(self.add_var_btn)
        self.scroll_layout.insertWidget(idx, row_widget)

        # Store references
        self.variable_color_pairs.append((variable_box, color_display, label_edit, row_widget))

    def add_proportion_plot(self):
        """Store current configuration (plot name, variable list, color list, label list)."""
        name = self.plot_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the proportion plot.")
            return

        variable_list = []
        color_list = []
        label_list = []
        for variable_box, color_display, label_edit, _ in self.variable_color_pairs:
            variable_list.append(variable_box.currentText())
            style = color_display.styleSheet()
            color = (
                style.split("background-color:")[-1].split(";")[0].strip()
                if "background-color" in style else "#cccccc"
            )
            color_list.append(color)
            label_text = label_edit.text().strip()
            label_list.append(label_text if label_text else variable_box.currentText())

        prop_info = {
            "name": name,
            "variable_list": variable_list,
            "color_list": color_list,
            "label_list": label_list
        }

        self.proportions.append(prop_info)

        # Add to list widget
        variables_str = ", ".join(f"{v} ({c})" for v, c in zip(variable_list, color_list))
        item_text = f"{name}: {variables_str}"
        self.proportions_list.addItem(QListWidgetItem(item_text))

        # Reset for next plot
        self.plot_name.clear()
        for _, color_display, _, _ in self.variable_color_pairs:
            color_display.setStyleSheet("background-color: #cccccc; border: 1px solid black;")

    def remove_selected_proportion(self):
        """Remove selected proportion configurations."""
        selected = self.proportions_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a proportion plot to remove.")
            return

        for item in selected:
            idx = self.proportions_list.row(item)
            self.proportions_list.takeItem(idx)
            self.proportions.pop(idx)

    def get_proportions(self):
        """Return user selections as structured dict."""
        return self.proportions

class GridSpecDialog(QDialog):
    def __init__(self, plot_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GridSpec Plot Configuration")
        self.resize(700, 500)

        self.plot_params = plot_params

        main_layout = QVBoxLayout(self)

        # Plot ordering
        order_group = QGroupBox("Plot Order (Drag to Reorder)")
        order_layout = QHBoxLayout(order_group)
        # Curves list
        self.curves_list = self._create_list_widget(plot_params.get("curves", []), "Curves")
        order_layout.addWidget(self.curves_list)
        # Time Series list
        self.series_list = self._create_list_widget(plot_params.get("time series", []), "Time Series")
        order_layout.addWidget(self.series_list)
        # Proportions list
        self.prop_list = self._create_list_widget(plot_params.get("proportions", []), "Proportions")
        order_layout.addWidget(self.prop_list)

        main_layout.addWidget(order_group)

        # GridSpec parameters
        config_group = QGroupBox("GridSpec Parameters")
        form = QFormLayout(config_group)

        self.width_ratios_edit = QLineEdit("1,3,5")
        self.height_ratios_edit = QLineEdit("30,1")
        self.wspace_edit = QLineEdit("0.5")
        self.hspace_edit = QLineEdit("0.2")

        form.addRow("Width ratios (curves, series, proportions):", self.width_ratios_edit)
        form.addRow("Height ratios (plots, legends):", self.height_ratios_edit)
        form.addRow("Horizontal space (wspace):", self.wspace_edit)
        form.addRow("Vertical space (hspace):", self.hspace_edit)

        main_layout.addWidget(config_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    # Helpers
    def _create_list_widget(self, items, title):
        group = QGroupBox(title)
        vlayout = QVBoxLayout(group)
        lw = QListWidget()
        lw.setDragDropMode(QListWidget.InternalMove)
        for obj in items:
            item = QListWidgetItem(obj.get("name", "Unnamed"))
            lw.addItem(item)
        vlayout.addWidget(lw)
        return group

    def get_gridspec_parameters(self):
        """Return user-configured GridSpec parameters."""
        try:
            width_ratios = [float(x.strip()) for x in self.width_ratios_edit.text().split(",") if x.strip()]
            height_ratios = [float(x.strip()) for x in self.height_ratios_edit.text().split(",") if x.strip()]
            wspace = float(self.wspace_edit.text())
            hspace = float(self.hspace_edit.text())

            # Retrieve reordered names from lists
            curves_order = [self.curves_list.findChild(QListWidget).item(i).text() 
                            for i in range(self.curves_list.findChild(QListWidget).count())]
            series_order = [self.series_list.findChild(QListWidget).item(i).text() 
                            for i in range(self.series_list.findChild(QListWidget).count())]
            prop_order = [self.prop_list.findChild(QListWidget).item(i).text() 
                          for i in range(self.prop_list.findChild(QListWidget).count())]

            return {
                "orders": {
                    "curves": curves_order,
                    "time series": series_order,
                    "proportions": prop_order,
                },
                "gridspec": {
                    "width_ratios": width_ratios,
                    "height_ratios": height_ratios,
                    "wspace": wspace,
                    "hspace": hspace,
                }
            }
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Check your numeric inputs:\n{e}")
            return None

# Canvas Tab
# class WellVisualizerFigure(FigureCanvas):
#     def __init__(self, plot_params, gridspec_params, parent=None):
#         fig = Figure(figsize=(width, height), dpi=dpi)
#         self.ax = fig.add_subplot(111)
#         super().__init__(fig)
#         self.setParent(parent)

#     def plot_well_data(self, well_data, plot_params):
#         """Plot well data according to the provided parameters."""
#         self.ax.clear()
#         # Example plotting logic (to be replaced with actual implementation)
#         for curve in plot_params.get("curves", []):
#             var = curve["variable"]
#             if var in well_data.columns:
#                 self.ax.plot(well_data["Depth"], well_data[var], label=curve["name"], color=curve["color"])
#         self.ax.set_xlabel("Depth")
#         self.ax.set_ylabel("Value")
#         self.ax.legend()
#         self.draw()

class WellPlotter:
    def __init__(self, figure: Figure):
        """
        Class responsible for plotting well logs, time series and proportions.
        It uses a Matplotlib Figure provided by the parent PyQt widget.
        """
        self.figure = figure
        self.df = None
        self.current_well = None
        self.selected_params = None
        self.gridspec_params = None

    # ----------------------------
    # DATA HANDLING
    # ----------------------------
    def load_data(self, filepath: str, sep: str = ";"):
        """Load CSV and clean numeric data (comma to dot)."""
        self.df = pd.read_csv(filepath, sep=sep, low_memory=False)
        for col in self.df.columns[1:]:
            self.df[col] = self.df[col].astype(str).str.replace(",", ".", regex=False)
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

    def set_well(self, well_name: str):
        """Define which well to plot."""
        if self.df is not None and well_name in self.df["Well Name"].unique():
            self.current_well = well_name
        else:
            raise ValueError("Invalid well name or dataset not loaded.")

    def set_plot_params(self, selected_params: dict, gridspec_params: dict):
        """Define what variables, colors, colormaps, etc. will be plotted."""
        self.selected_params = selected_params
        self.gridspec_params = gridspec_params

    # ----------------------------
    # PLOTTING FUNCTION
    # ----------------------------
    def plot(self):
        """Generate the plot in the provided Figure."""
        if any(v is None for v in [self.df, self.current_well, self.selected_params, self.gridspec_params]):
            raise RuntimeError("Data, well, or parameters not set before plotting.")

        self.figure.clear()

        well_df = self.df.loc[self.df['Well Name'] == self.current_well, :].copy()
        depths = well_df['TVD'].values
        depth_max, depth_min = np.nanmax(depths), np.nanmin(depths)

        n_curves = len(self.selected_params['curves'])
        n_series = len(self.selected_params['time series'])
        n_proportions = len(self.selected_params['proportions'])
        n_cols = n_curves + n_series + n_proportions

        width_ratios = []
        for w, i in zip(self.gridspec_params['gridspec']['width_ratios'], [n_curves, n_series, n_proportions]):
            width_ratios += [w] * i

        gs = GridSpec(
            2, n_cols,
            figure=self.figure,
            width_ratios=width_ratios,
            height_ratios=self.gridspec_params['gridspec']['height_ratios'],
            wspace=self.gridspec_params['gridspec']['wspace'],
            hspace=self.gridspec_params['gridspec']['hspace']
        )

        # ---- Curves ----
        for i, curve in enumerate(self.selected_params['curves']):
            ax = self.figure.add_subplot(gs[0, i])
            curve_data = well_df[curve['variable']].values
            ax.plot(curve_data, depths, color=curve['color'], linewidth=0.8)
            ax.set_xlabel(curve['unit'], fontsize=6)
            ax.grid(True, linestyle=":", alpha=0.4)
            ax.set_ylim(depth_max, depth_min)
            finite_data = curve_data[np.isfinite(curve_data)]
            if len(finite_data) > 0:
                xmin, xmax = np.nanpercentile(finite_data, [2, 98])
                ax.set_xlim(xmin, xmax)
            if i == 0:
                ax.set_ylabel('Depth (m)')
            else:
                ax.set_yticklabels([])
            ax.set_title(curve['name'], fontsize=6, pad=4)

        # ---- Time Series ----
        for i, series in enumerate(self.selected_params['time series']):
            time_cols = well_df.loc[:, series['start_col']:series['end_col']].columns
            times = time_cols.to_series().str.extract(r'([\d\.eE+-]+)').astype(float)[0].values
            data = well_df.loc[:, series['start_col']:series['end_col']].values
            ax = self.figure.add_subplot(gs[0, n_curves + i])
            pcm = ax.pcolormesh(times, depths, data, shading='auto', cmap=series['colormap'])
            if series['logscale']:
                ax.set_xscale('log')
            ax.set_xlabel('Time')
            ax.set_ylim(depth_max, depth_min)
            ax.set_title(series['name'], fontsize=6, pad=4)
            ax0 = self.figure.add_subplot(gs[1, n_curves + i])
            cbar = plt.colorbar(pcm, cax=ax0, orientation='horizontal', pad=0.15, fraction=0.05)

        # ---- Proportions ----
        for i, prop in enumerate(self.selected_params['proportions']):
            well_df["sum_elements"] = well_df[prop['variable_list']].sum(axis=1)
            for var in prop['variable_list']:
                well_df[f"{var}_prop"] = well_df[var] / well_df["sum_elements"]
            well_df = well_df.sort_values("TVD").reset_index(drop=True)
            depths = well_df["TVD"].values
            ax = self.figure.add_subplot(gs[0, n_curves + n_series + i])
            bottom = np.zeros(len(well_df))
            for var, color, label in zip(prop['variable_list'], prop['color_list'], prop['label_list']):
                ax.barh(depths, well_df[f"{var}_prop"], left=bottom, color=color, label=label)
                bottom += well_df[f"{var}_prop"].values
            ax.set_xlim(0, 1)
            ax.set_ylim(depth_max, depth_min)
            if (n_curves + n_series + i) > 0:
                ax.set_yticklabels([])
            ax.set_title(prop['name'], fontsize=6, pad=4)
            ax_leg = self.figure.add_subplot(gs[1, n_curves + n_series + i])
            ax_leg.axis("off")
            handles, labels = ax.get_legend_handles_labels()
            ax_leg.legend(handles, labels, loc="center", ncol=1, frameon=False)

        # ---- Final adjustments ----
        self.figure.suptitle(f"Well: {self.current_well}", fontsize=8)
        self.figure.tight_layout()
        self.figure.canvas.draw_idle()