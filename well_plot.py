from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QDialog, QPushButton, QLabel, QListWidget, QGroupBox, 
    QComboBox, QFormLayout, QSpinBox, QLineEdit, QDialogButtonBox,
    QListWidgetItem, QColorDialog, QMessageBox, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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
class WellVisualizerFigure(FigureCanvas):
    def __init__(self, plot_params, gridspec_params, parent=None):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def plot_well_data(self, well_data, plot_params):
        """Plot well data according to the provided parameters."""
        self.ax.clear()
        # Example plotting logic (to be replaced with actual implementation)
        for curve in plot_params.get("curves", []):
            var = curve["variable"]
            if var in well_data.columns:
                self.ax.plot(well_data["Depth"], well_data[var], label=curve["name"], color=curve["color"])
        self.ax.set_xlabel("Depth")
        self.ax.set_ylabel("Value")
        self.ax.legend()
        self.draw()