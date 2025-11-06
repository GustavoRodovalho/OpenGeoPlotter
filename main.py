import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QTableView, QLabel, QDialog, QTabWidget, QHBoxLayout, QListWidget, QButtonGroup, QRadioButton, QGroupBox, QMessageBox, QToolButton, QStyle, QComboBox
from PyQt5.QtCore import QAbstractTableModel, Qt
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
        table_layout = QVBoxLayout()
        # Table widget
        self.table = QTableView()
        self.table.clicked.connect(self.handle_column_click) # replace for handle column click and opening a QDialog with the statistics for numeric columns (int or float)
        table_layout.addWidget(self.table)
        # Dataset shape
        self.dataset_shape = QLabel("Dataset shape:")
        table_layout.addWidget(self.dataset_shape)
        # Well counter widget
        self.well_count = QLabel("Number of wells:")
        table_layout.addWidget(self.well_count)
        # Missing values counter widget
        self.missing_count = QLabel("Missing values:")
        table_layout.addWidget(self.missing_count)
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
        info_btn = QToolButton()
        info_btn.setToolTip("Left-click on the canvas to make a selection.\nRight-click anywhere to clear selected wells.")
        info_btn.setCursor(Qt.PointingHandCursor)
        info_btn.setAutoRaise(True)
        info_btn.setFixedSize(16, 16)
        # Use the platform's standard "information" icon
        info_icon = info_btn.style().standardIcon(QStyle.SP_MessageBoxInformation)
        info_btn.setIcon(info_icon)
        info_btn.setIconSize(info_btn.size() * 0.8)
        info_layout.addWidget(info_btn)
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
        self.well_depth_list = QListWidget()
        self.remove_selection = QPushButton("Remove selected depths")
        sidebar_menu.addWidget(self.add_button)
        sidebar_menu.addWidget(QLabel("Wells"))
        sidebar_menu.addWidget(self.well_combo)
        sidebar_menu.addWidget(QLabel("Well depths"))
        sidebar_menu.addWidget(self.well_depth_list)
        sidebar_menu.addWidget(self.remove_selection)
        sidebar_menu_box = QGroupBox("Plots Settings")
        sidebar_menu_box.setMaximumWidth(200)
        sidebar_menu_box.setLayout(sidebar_menu)
        # Log Viewer widget
        self.log_viewer = LogViewer()
        self.add_button.clicked.connect(self.add_tracks)
        self.well_combo.currentTextChanged.connect(self.update_log_viewer)
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
                self.table.setModel(model)

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

    def handle_column_click(self, index):
        if self.df is not None and index.isValid():
            column = self.df.columns[index.column()]
            missing = self.df[column].isna().sum()
            self.missing_count.setText(f"Missing values in {column}: {missing}")

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
                selected_curves = dialog.get_selected_curves()
                if selected_curves:
                    print("User selected tracks:", selected_curves)
                    # Save the selection in an attribute or pass to your LogViewer
                    self.selected_tracks = selected_curves
                    # Now add unique wells in the Combo Box
                    self.well_combo.clear()
                    well_column = self.selected_columns.get("Well ID")
                    self.unique_wells = self.df[well_column].dropna().unique()
                    self.well_combo.addItems([""]+[str(well) for well in self.unique_wells])
                    # When the user select an item in the Combo Box, update the LogViewer with the selected tracks for that well
                    # self.log_viewer.add_tracks(selected_curves)

    def update_log_viewer(self, well_name):
        if well_name.strip():
            df_well = self.df[self.df[self.selected_columns.get("Well ID")] == well_name]
            df_depths = df_well[[self.selected_columns.get("Depth")]]
            df_curves = df_well[[col for col in self.selected_tracks if col in df_well.columns]]
            self.log_viewer.update_tracks(df_depths, df_curves)
        #     df_well = self.df[self.df[well_column] == well_id]
        #     self.log_viewer.add_tracks(df_well, depth_column, selected_curves)
        # else:
        #     self.log_viewer.clear_tracks()

    # def add_plots(self):
    #     if self.df is not None and self.selected_columns is not None:
    #         remaining_columns = [col for col in self.df.columns if col not in set(col for col in self.selected_columns.values() if col)]
    #         if not hasattr(self, "plot_config_dialog") or self.plot_config_dialog is None:
    #             self.plot_config_dialog = PlotConfigDialog(self.df, remaining_columns, self)
    #         dialog = self.plot_config_dialog
    #         # Reuse existing dialog with current data
    #         dialog.remaining_columns = remaining_columns
    #         if dialog.exec_() == QDialog.Accepted:
    #             self.plots_params = dialog.get_parameters()
    #             print("User selected parameters:", self.plots_params)
    #             # Populate well list combo box
    #             well_column = self.selected_columns.get("Well ID")
    #             if well_column and well_column in self.df.columns:
    #                 self.unique_wells = self.df[well_column].dropna().unique()
    #                 self.well_combo.clear()
    #                 self.well_combo.addItems([str(well) for well in self.unique_wells])

    # def gridspec_settings(self):
    #     if self.df is not None and self.selected_columns is not None and self.plots_params is not None:
    #         dialog = GridSpecDialog(self.plots_params, self)
    #         if dialog.exec_() == QDialog.Accepted:
    #             self.gridspec_params = dialog.get_gridspec_parameters()
    #             print("User selected GridSpec parameters:", self.gridspec_params)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())