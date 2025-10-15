import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QTableView, QLabel, QDialog, QTabWidget, QHBoxLayout, QListWidget, QButtonGroup, QRadioButton, QGroupBox, QMessageBox, QComboBox
from PyQt5.QtCore import QAbstractTableModel, Qt
from load_csv import LoadCSVDialog, CSVOptions, VariableTypeDialog
from loc_plot import LocalizationMap
# from well_plot import WellGridSpec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
        self.table.clicked.connect(self.handle_column_click)
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
        radio_group.addButton(self.latlon_radio)
        radio_group.addButton(self.xy_radio)
        sidebar.addWidget(self.latlon_radio)
        sidebar.addWidget(self.xy_radio)
        # Selected wells
        self.point_list = QListWidget()
        sidebar.addWidget(QLabel("Selected wells"))
        sidebar.addWidget(self.point_list)
        clear_button = QPushButton("Clear selection")
        clear_button.clicked.connect(self.point_list.clear)
        sidebar.addWidget(clear_button)
        split_dataset = QPushButton("Split dataset")
        split_dataset.clicked.connect(self.export_selected_wells)
        sidebar.addWidget(split_dataset)
        sidebar_box = QGroupBox("Options")
        sidebar_box.setMaximumWidth(200)
        sidebar_box.setLayout(sidebar)
        # 2.2. Map widget
        self.map_layout = QVBoxLayout()
        self.map_canvas = LocalizationMap(self.df, self.selected_columns, self.map_layout, self.point_list)
        # Assemble layouts
        combined_layout = QHBoxLayout()
        combined_layout.addWidget(sidebar_box)
        combined_layout.addLayout(self.map_layout)
        self.loc_tab.setLayout(combined_layout)
        self.tabs.addTab(self.loc_tab, "Localization Map")

        # Tab 3: Well visualizer
        self.visualizer_tab = QWidget()
        sidebar_menu = QVBoxLayout()
        self.update_button = QPushButton("Update Plots")
        sidebar_menu.addWidget(self.update_button)
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
        self.visualizer_tab.setLayout(full_layout)
        self.tabs.addTab(self.visualizer_tab, "Well Visualizer")

        self.setLayout(main_layout)

    def handle_column_click(self, index):
        if self.df is not None and index.isValid():
            column = self.df.columns[index.column()]
            missing = self.df[column].isna().sum()
            self.missing_count.setText(f"Missing values in {column}: {missing}")

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
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
                    self.selected_columns = options_dialog.get_selected_columns()
                    well_column = self.selected_columns.get("Well ID")
                    if well_column and well_column in self.df.columns:
                        num_wells = self.df[well_column].nunique()
                        self.well_list = self.df[well_column].unique()
                        self.well_count.setText(f"Number of wells: {num_wells}")
                    else:
                        self.well_count.setText("Number of wells:")

                # Variables types
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

                # Check available coordinate types
                has_latlon = (
                    self.selected_columns.get("Latitude") in self.df.columns and
                    self.selected_columns.get("Longitude") in self.df.columns
                )
                has_xy = (
                    self.selected_columns.get("X") in self.df.columns and
                    self.selected_columns.get("Y") in self.df.columns
                )

                # Disable unavailable options
                self.latlon_radio.setEnabled(has_latlon)
                self.xy_radio.setEnabled(has_xy)

                # If neither coordinate type is available, disable the entire map tab
                if not has_latlon and not has_xy:
                    idx = self.tabs.indexOf(self.loc_tab)
                    if idx != -1:
                        self.tabs.setTabEnabled(idx, False)
                    QMessageBox.warning(
                        self,
                        "Missing coordinates",
                        "Neither Latitude/Longitude nor X/Y coordinate columns were specified."
                    )
                    return

                # Default coordinate type (prioritize Lat/Lon if available)
                if has_latlon:
                    self.latlon_radio.setChecked(True)
                    self.plot_localization_map("Latitude/Longitude")
                elif has_xy:
                    self.xy_radio.setChecked(True)
                    self.plot_localization_map("X/Y")

                # Connect radio buttons
                self.latlon_radio.toggled.connect(lambda: self.plot_localization_map("Latitude/Longitude"))
                self.xy_radio.toggled.connect(lambda: self.plot_localization_map("X/Y"))

    def plot_localization_map(self, mode):
        # Update data and replot without recreating the canvas
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

    def update_plot_settings(self):
        if self.selected_columns is not None:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())