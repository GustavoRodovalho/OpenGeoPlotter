import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton,
    QTableView, QLabel, QDialog, QTabWidget, QHBoxLayout,
    QListWidget, QButtonGroup, QRadioButton, QGroupBox, QMessageBox,
    QToolButton, QStyle, QComboBox, QTreeWidget, QTreeWidgetItem,
    QGraphicsRectItem, QLineEdit, QDialogButtonBox
)
from PyQt5.QtCore import QAbstractTableModel, Qt
import pyqtgraph as pg
import numpy as np
from options_csv import LoadCSVDialog, CSVOptions, VariableTypeDialog
from loc_plot import LocalizationMap
# from well_plot import PlotConfigDialog, GridSpecDialog, WellPlotter
from log_viewer import LogViewer, TrackSelectionDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._df.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(self._df.index[section])
        return None

class InfoBtn(QToolButton):
    def __init__(self, tooltip_text):
        super().__init__()
        self.setToolTip(tooltip_text)
        self.setCursor(Qt.PointingHandCursor)
        self.setAutoRaise(True)
        self.setFixedSize(16, 16)
        # Use the platform's standard "information" icon
        info_icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        self.setIcon(info_icon)
        self.setIconSize(self.size() * 0.8)

class WellLoggingViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Well Logging Viewer")
        self.setGeometry(100, 100, 1000, 600)

        self.df = None
        self.selected_columns = {}

        main_layout = QVBoxLayout()
        self.button = QPushButton("Load CSV")
        self.button.clicked.connect(self.load_csv)
        main_layout.addWidget(self.button)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Data Table
        self.table_tab = QWidget()
        table_layout = QHBoxLayout()
        # Sidebar (initially hidden)
        self.var_sidebar = QWidget()
        self.var_sidebar.setFixedWidth(300)
        self.sidebar_layout = QVBoxLayout()
        self.var_sidebar.setLayout(self.sidebar_layout)
        # Distribution type selector
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Histogram", "Boxplot"])
        self.plot_type_combo.currentTextChanged.connect(self.update_plot_type)
        self.sidebar_layout.addWidget(self.plot_type_combo)
        # Plot area
        self.var_plot = pg.PlotWidget()
        self.var_plot.setBackground("w")
        self.sidebar_layout.addWidget(self.var_plot, stretch=1)
        # Missing values label
        self.missing_label = QLabel("Missing values: 0")
        self.sidebar_layout.addWidget(self.missing_label)
        # Filter and replace button
        self.replace_button = QPushButton("Filter and replace values")
        self.replace_button.clicked.connect(self.filter_and_replace_values)
        self.sidebar_layout.addWidget(self.replace_button)
        # Export to CSV button
        self.export_button = QPushButton("Export modified data to CSV")
        self.export_button.clicked.connect(self.export_modified_data)
        self.sidebar_layout.addWidget(self.export_button)
        # Hide sidebar initially
        self.var_sidebar.hide()
        # Table
        self.table = QTableView()
        header = self.table.horizontalHeader()
        header.sectionClicked.connect(self.handle_header_click)
        self.table_view_layout = QVBoxLayout()
        self.table_view_layout.addWidget(self.table)
        # Info labels below table
        self.dataset_shape = QLabel("Dataset shape:")
        self.well_count = QLabel("Number of wells:")
        for w in [self.dataset_shape, self.well_count]:
            self.table_view_layout.addWidget(w)
        # Combine
        table_layout.addWidget(self.var_sidebar)
        table_layout.addLayout(self.table_view_layout)
        self.table_tab.setLayout(table_layout)
        self.tabs.addTab(self.table_tab, "Dataset")

        # Tab 2: Localization map
        self.loc_tab = QWidget()
        # 2.1. Options sidebar
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Coordinate type"))
        radio_group = QButtonGroup(self.loc_tab)
        self.latlon_radio = QRadioButton("Latitude/Longitude")
        self.xy_radio = QRadioButton("X/Y")
        # Connect radio buttons in localization map
        self.latlon_radio.toggled.connect(lambda: self.plot_localization_map("Latitude/Longitude"))
        self.xy_radio.toggled.connect(lambda: self.plot_localization_map("X/Y"))
        radio_group.addButton(self.latlon_radio)
        radio_group.addButton(self.xy_radio)
        sidebar.addWidget(self.latlon_radio)
        sidebar.addWidget(self.xy_radio)
        # Selected wells
        self.point_list = QListWidget()
        info_layout = QHBoxLayout()
        select_label = QLabel("Selected wells")
        info_layout.addWidget(select_label)
        loc_info_btn = InfoBtn(
            tooltip_text="Left-click on the canvas to make a selection.\nRight-click anywhere to clear selected wells.")
        info_layout.addWidget(loc_info_btn)
        info_layout.addStretch()
        sidebar.addLayout(info_layout)
        sidebar.addWidget(self.point_list)
        split_dataset = QPushButton("Split dataset")
        split_dataset.clicked.connect(self.export_selected_wells)
        sidebar.addWidget(split_dataset)
        sidebar_box = QGroupBox("Options")
        sidebar_box.setMaximumWidth(200)
        sidebar_box.setLayout(sidebar)
        # 2.2. Map widget
        self.map_layout = QVBoxLayout()
        self.map_canvas = LocalizationMap(self.df, self.selected_columns, self.map_layout, self.point_list)
        toolbar = NavigationToolbar(self.map_canvas, self)
        self.map_layout.addWidget(toolbar)
        # Assemble layouts
        combined_layout = QHBoxLayout()
        combined_layout.addWidget(sidebar_box)
        combined_layout.addLayout(self.map_layout)
        self.loc_tab.setLayout(combined_layout)
        self.tabs.addTab(self.loc_tab, "Localization Map")

        # Tab 3: Well Viewer
        self.visualizer_tab = QWidget()
        sidebar_menu = QVBoxLayout()
        self.add_button = QPushButton("Add Tracks")
        self.well_combo = QComboBox()
        self.well_depth_list = QTreeWidget()
        self.well_depth_list.setHeaderLabels(["Well", "Depth ranges"])
        self.well_depth_list.setColumnCount(2)
        self.remove_selection = QPushButton("Remove selected depth ranges")
        sidebar_menu.addWidget(self.add_button)
        sidebar_menu.addWidget(QLabel("Wells"))
        sidebar_menu.addWidget(self.well_combo)
        # Add depths selection label and info button
        info_depths_layout = QHBoxLayout()
        select_depths_label = QLabel("Selected depths")
        info_depths_layout.addWidget(select_depths_label)
        log_info_btn = InfoBtn(
            tooltip_text="Left-click on the tracks to make a selection.\nRight-click to clear the selected depth range.")
        info_depths_layout.addWidget(log_info_btn)
        info_depths_layout.addStretch()
        sidebar_menu.addLayout(info_depths_layout)
        # Add list widget and remove button
        sidebar_menu.addWidget(self.well_depth_list)
        sidebar_menu.addWidget(self.remove_selection)
        sidebar_menu_box = QGroupBox("Plots Settings")
        sidebar_menu_box.setMaximumWidth(250)
        sidebar_menu_box.setLayout(sidebar_menu)
        # Log Viewer widget
        self.log_viewer = LogViewer()
        self.add_button.clicked.connect(self.add_tracks)
        self.well_combo.currentTextChanged.connect(self.update_log_viewer)
        self.remove_selection.clicked.connect(self.remove_selected_depth_ranges)
        # Assemble layouts
        full_layout = QHBoxLayout()
        full_layout.addWidget(sidebar_menu_box)
        full_layout.addWidget(self.log_viewer)
        self.visualizer_tab.setLayout(full_layout)
        # Add to main tabs
        self.tabs.addTab(self.visualizer_tab, "Well Viewer")

        self.setLayout(main_layout)

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.df = None
            # Load .csv dialog
            dialog = LoadCSVDialog()
            if dialog.exec_() == QDialog.Accepted:
                sep, header, low_memory = dialog.get_options()
                self.df = pd.read_csv(file_path, sep=sep, header=header, low_memory=low_memory)
                self.dataset_shape.setText(f"Dataset shape: {self.df.shape[0]} x {self.df.shape[1]}")
                model = PandasModel(self.df)
                self.model = model
                self.table.setModel(self.model)

                # Show .csv options dialog
                options_dialog = CSVOptions(self.df)
                if options_dialog.exec_() == QDialog.Accepted:
                    self.selected_columns = options_dialog.get_selected_columns() # Well ID, Depth and coordinates
                    well_column = self.selected_columns.get("Well ID")
                    if well_column and well_column in self.df.columns:
                        num_wells = self.df[well_column].nunique()
                        self.well_count.setText(f"Number of wells: {num_wells}")
                    else:
                        self.well_count.setText("Number of wells:")

                # Variables types
                # Transform depth and coordinates into numeric
                depth_col = self.selected_columns.get("Depth")
                if depth_col and depth_col in self.df.columns:
                    self.df[depth_col] = pd.to_numeric(self.df[depth_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
                if "Latitude" in self.selected_columns:
                    lat_col = self.selected_columns.get("Latitude")
                    lon_col = self.selected_columns.get("Longitude")
                    if lat_col and lon_col and lat_col in self.df.columns and lon_col in self.df.columns:
                        self.df[lon_col] = pd.to_numeric(self.df[lon_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
                        self.df[lat_col] = pd.to_numeric(self.df[lat_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
                if "X" in self.selected_columns:
                    x_col = self.selected_columns.get("X")
                    y_col = self.selected_columns.get("Y")
                    if x_col and y_col and x_col in self.df.columns and y_col in self.df.columns:
                        self.df[x_col] = pd.to_numeric(self.df[x_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
                        self.df[y_col] = pd.to_numeric(self.df[y_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
                # Transform other selected columns based on user input
                type_dialog = VariableTypeDialog(self.df, self.selected_columns)
                if type_dialog.exec_() == QDialog.Accepted:
                    type_map = type_dialog.get_type_map()
                for col, dtype in type_map.items():
                    try:
                        if dtype in ["int", "float"]:
                            self.df[col] = self.df[col].astype(str).str.replace(",", ".", regex=False)
                            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                            if dtype == "int":
                                self.df[col] = self.df[col].astype("Int64")
                        elif dtype == "str":
                            self.df[col] = self.df[col].astype(str)
                    except Exception as e:
                        print(f"Could not convert column {col} to {dtype}: {e}")

    def update_plot_type(self, plot_type):
        """Update the plot when the user changes the combo box."""
        self.current_plot_type = plot_type
        if hasattr(self, "current_column"):
            col_idx = self.df.columns.get_loc(self.current_column)
            self.handle_header_click(col_idx)

    def handle_header_click(self, logicalIndex):
        """Visualize selected column depending on plot type."""
        self._df = self.df.copy() # Copy for the user to modify
        col_name = self._df.columns[logicalIndex]
        self.current_column = col_name
        series = self._df[col_name]

        # Show sidebar
        self.var_sidebar.show()
        self.var_plot.clear()
        self.var_plot.showGrid(y=True, x=True)
        # Missing values
        missing_count = series.isna().sum()
        self.missing_label.setText(f"Missing values: {missing_count}")
        self.current_column = col_name
        # Default plot type
        plot_type = self.plot_type_combo.currentText()

        if not pd.api.types.is_numeric_dtype(series):
            self.var_plot.setTitle("Non-numeric column")
            self.replace_button.setEnabled(False)
            return

        clean_data = series.dropna().values
        if len(clean_data) == 0:
            self.var_plot.setTitle("No valid data")
            return

        self.replace_button.setEnabled(True)

        if plot_type == "Histogram":
            y, x = np.histogram(clean_data, bins="auto")
            bg = pg.BarGraphItem(x=x[:-1], height=y, width=np.diff(x), brush="skyblue")
            self.var_plot.addItem(bg)
            self.var_plot.setLabel("bottom", col_name)
            self.var_plot.setLabel("left", "Count")
            self.var_plot.setTitle("")
            self.var_plot.showGrid(x=True, y=True, alpha=0.3)
            axis_bottom = self.var_plot.getAxis("bottom")
            axis_bottom.enableAutoSIPrefix(False)
            axis_bottom.setStyle(tickTextOffset=10)

        elif plot_type == "Boxplot":
            q1, q2, q3 = np.percentile(clean_data, [25, 50, 75])
            iqr = q3 - q1
            lw = np.min(clean_data[clean_data >= q1 - 1.5 * iqr])
            uw = np.max(clean_data[clean_data <= q3 + 1.5 * iqr])

            # Box rectangle
            box = QGraphicsRectItem(0.5, q1, 1, q3 - q1)
            box.setPen(pg.mkPen(color="k", width=1))
            box.setBrush(pg.mkBrush(200, 200, 255, 150))
            self.var_plot.addItem(box)
            # Median line
            self.var_plot.addItem(pg.InfiniteLine(pos=q2, angle=0, pen=pg.mkPen('r', width=2)))
            # Whiskers
            for y in [lw, uw]:
                self.var_plot.addItem(pg.InfiniteLine(pos=y, angle=0, pen=pg.mkPen('k', width=1)))
            self.var_plot.addItem(pg.PlotDataItem([1, 1], [q3, uw], pen=pg.mkPen('k')))
            self.var_plot.addItem(pg.PlotDataItem([1, 1], [q1, lw], pen=pg.mkPen('k')))

            self.var_plot.addItem(pg.ScatterPlotItem(
                x=[1]*len(clean_data),
                y=clean_data,
                pen=None,
                brush=pg.mkBrush(100, 100, 255, 120),
                size=6
            ))

            self.var_plot.setLabel("bottom", "")
            self.var_plot.setLabel("left", col_name)
            self.var_plot.setTitle("")

    def filter_and_replace_values(self):
        """Ask user for min/max values and clip the selected column accordingly."""
        if not hasattr(self, "current_column"):
            QMessageBox.warning(self, "No Column Selected", "Please select a column first.")
            return

        col = self.current_column
        df = self.model._df

        if not pd.api.types.is_numeric_dtype(df[col]):
            QMessageBox.warning(self, "Invalid Column", f"The column '{col}' is not numeric.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Filter values in '{col}'")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"Enter min and max allowed values for '{col}':"))
        min_input = QLineEdit()
        max_input = QLineEdit()
        min_input.setPlaceholderText("Minimum value (leave empty for no limit)")
        max_input.setPlaceholderText("Maximum value (leave empty for no limit)")

        layout.addWidget(QLabel("Minimum value:"))
        layout.addWidget(min_input)
        layout.addWidget(QLabel("Maximum value:"))
        layout.addWidget(max_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec_() != QDialog.Accepted:
            return

        try:
            min_val = float(min_input.text()) if min_input.text() else None
            max_val = float(max_input.text()) if max_input.text() else None
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")
            return

        # Apply clipping
        if min_val is not None:
            df.loc[df[col] < min_val, col] = min_val
        if max_val is not None:
            df.loc[df[col] > max_val, col] = max_val

        self._df = df
        self.model.layoutChanged.emit()
        self.handle_header_click(df.columns.get_loc(col))

        QMessageBox.information(self, "Values Updated", f"Values in '{col}' were filtered to the range [{min_val}, {max_val}].")

    def export_modified_data(self):
        """Open a save dialog and export the modified DataFrame to a CSV file."""
        if not hasattr(self, "_df") or self._df is None or self._df.empty:
            QMessageBox.warning(self, "No Data", "There is no modified data to export.")
            return

        # Open file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Filtered Dataset",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        # Save based on extension
        try:
            if file_path.endswith(".xlsx"):
                self._df.to_excel(file_path, index=False)
            else:
                # Default: save as CSV
                if not file_path.endswith(".csv"):
                    file_path += ".csv"
                self._df.to_csv(file_path, index=False)

            QMessageBox.information(self, "Success", f"Dataset exported successfully:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export dataset:\n{str(e)}")

    def plot_localization_map(self, mode):
        if self.df is not None:
            if mode == "Latitude/Longitude":
                if self.selected_columns.get("Latitude") in self.df.columns and self.selected_columns.get("Longitude") in self.df.columns:
                    self.map_canvas.df = self.df
                    self.map_canvas.selected_columns = self.selected_columns
                    self.map_canvas.plot_localization(mode)
            if mode == "X/Y":
                if self.selected_columns.get("X") in self.df.columns and self.selected_columns.get("Y") in self.df.columns:
                    self.map_canvas.df = self.df
                    self.map_canvas.selected_columns = self.selected_columns
                    self.map_canvas.plot_localization(mode)

    def export_selected_wells(self):
        # Export two DataFrames: one with selected wells in the list widget and another with the remaining wells
        if self.point_list.count() > 0:
            if self.df is None or not hasattr(self, "selected_columns"):
                QMessageBox.warning(self, "No dataset", "Please load a CSV file first")
                return
            well_col = self.selected_columns.get("Well ID")
            if well_col is None or well_col not in self.df.columns:
                QMessageBox.warning(self, "Missing Well ID", "The 'Well ID' column must be specified")
                return
            all_items = [self.point_list.item(i).text() for i in range(self.point_list.count())]
            df_selected = self.df[self.df[well_col].isin(all_items)].copy()
            df_remaining = self.df[~self.df[well_col].isin(all_items)].copy()
            selected_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save selected wells CSV",
                "selected_wells.csv",
                "CSV Files (*.csv)"
            )
            if selected_path:
                remaining_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save remaining wells CSV",
                    "remaining_wells.csv",
                    "CSV Files (*.csv)"
                )
                if remaining_path:
                    df_selected.to_csv(selected_path, index=False)
                    df_remaining.to_csv(remaining_path, index=False)
                    QMessageBox.information(
                        self,
                        "Export successful",
                        f"Selected wells saved to:\n{selected_path}\n\n"
                        f"Remaining wells saved to:\n{remaining_path}"
                    )
        else:
            return

    def load_wells(self):
        self.well_combo.clear()
        self.well_combo.addItems([str(well) for well in self.well_list])

    def add_tracks(self):
        if self.df is not None and self.selected_columns is not None:
            dialog = TrackSelectionDialog(self.df, self.selected_columns, self)
            if dialog.exec_() == QDialog.Accepted:
                # Reset log viewer and well depth list to default
                self.log_viewer.reset_viewer(clear_all_wells=True)
                self.well_depth_list.clear()
                # Get curves for tracks
                selected_curves = dialog.get_selected_curves()
                if selected_curves:
                    self.selected_tracks = selected_curves
                    # Now add unique wells in the Combo Box
                    self.well_combo.clear()
                    well_column = self.selected_columns.get("Well ID")
                    self.unique_wells = self.df[well_column].dropna().unique()
                    self.well_combo.addItems([""]+[str(well) for well in self.unique_wells])

    def update_log_viewer(self, well_name):
        if well_name.strip():
            df_well = self.df[self.df[self.selected_columns.get("Well ID")] == well_name]
            df_depths = df_well[[self.selected_columns.get("Depth")]]
            df_curves = df_well[[col for col in self.selected_tracks if col in df_well.columns]]
            self.log_viewer.update_tracks(well_name, df_depths, df_curves)

    def update_well_depth_list(self):
        self.well_depth_list.clear()
        for well, regions in self.log_viewer.well_regions.items():
            if not regions:
                continue
            well_item = QTreeWidgetItem([well])
            for reg in regions:
                y_min = reg.get("y_min", 0.0)
                y_max = reg.get("y_max", 0.0)
                child = QTreeWidgetItem(["", f"{y_min:.2f} – {y_max:.2f}"])
                well_item.addChild(child)
            self.well_depth_list.addTopLevelItem(well_item)
        self.well_depth_list.expandAll()

    def remove_selected_depth_ranges(self):
        """Filter out depths inside the selected ranges and let the user save as a new CSV."""
        # Check if data and regions exist and are valid
        if (
            getattr(self, "df", None) is not None
            and not self.df.empty
            and hasattr(self, "selected_columns")
            and hasattr(self.log_viewer, "well_regions")
            and self.log_viewer.well_regions
        ):
            well_col = self.selected_columns.get("Well ID")
            depth_col = self.selected_columns.get("Depth")

            if well_col in self.df.columns and depth_col in self.df.columns:
                df_filtered = self.df.copy()
                initial_count = len(df_filtered)

                # Loop through wells and regions
                for well, regions in self.log_viewer.well_regions.items():
                    if not regions:
                        continue

                    # Keep only rows outside the selected regions
                    keep_mask = pd.Series(True, index=df_filtered.index)
                    for reg in regions:
                        y_min = reg.get("y_min")
                        y_max = reg.get("y_max")
                        in_range = (df_filtered[depth_col] >= y_min) & (df_filtered[depth_col] <= y_max)
                        keep_mask &= ~((df_filtered[well_col] == well) & in_range)
                    df_filtered = df_filtered[keep_mask]

                removed_count = initial_count - len(df_filtered)

                # Ask where to save
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save filtered data as CSV",
                    "",
                    "CSV Files (*.csv);;All Files (*)"
                )

                if save_path:
                    df_filtered.to_csv(save_path, index=False)
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Filtered data saved to:\n{save_path}\n\nRemoved {removed_count} rows."
                    )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())