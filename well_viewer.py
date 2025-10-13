import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QTableView, QLabel, QDialog, QTabWidget, QHBoxLayout, QListWidget, QStackedWidget
from PyQt5.QtCore import QAbstractTableModel, Qt
from load_csv import LoadCSVDialog, CSVOptions, VariableTypeDialog
from plot_manager import LocalizationMap
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

        # Tab 2: Localization Map
        self.plot_tab = QWidget()
        plot_layout = QHBoxLayout()
        # Sidebar menu
        self.plot_menu = QListWidget()
        self.plot_menu.addItem("Latitude/Longitude")
        self.plot_menu.addItem("X/Y")
        self.plot_menu.setFixedWidth(150)
        self.plot_menu.currentRowChanged.connect(self.switch_plot_view)
        plot_layout.addWidget(self.plot_menu)

        # Stacked widget to hold different
        self.plot_stack = QStackedWidget()

        # Localization Map view
        self.localization_view = QWidget()
        self.localization_layout = QVBoxLayout()
        self.localization_view.setLayout(self.localization_layout)
        self.plot_stack.addWidget(self.localization_view)

        # Statistics view
        self.statistics_view = QWidget()
        self.statistics_layout = QVBoxLayout()
        self.statistics_view.setLayout(self.statistics_layout)
        self.plot_stack.addWidget(self.statistics_view)

        plot_layout.addWidget(self.plot_stack)
        self.plot_tab.setLayout(plot_layout)
        self.tabs.addTab(self.plot_tab, "Localization Map")

        self.setLayout(main_layout)

    def handle_column_click(self, index):
        if self.df is not None and index.isValid():
            column = self.df.columns[index.column()]
            missing = self.df[column].isna().sum()
            self.missing_count.setText(f"Missing values in {column}: {missing}")

    def switch_plot_view(self, index):
        self.plot_stack.setCurrentIndex(index)
        if index == 0:
            mode = "Latitude/Longitude"
        elif index == 1: 
            mode = "X/Y"
        self.plot_localization_map(mode)

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
                        print(f"Unique wells: {self.df[well_column].unique()}")
                        self.well_count.setText(f"Number of wells: {num_wells}")
                    else:
                        self.well_count.setText("Number of wells:")
                    print("User selected columns:", self.selected_columns)

                # Variables settings
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

                # Plot statistics in the plot tab
                # self.plot_variable_statistics()

    def plot_localization_map(self, mode):
        plotter = LocalizationMap(self.df, self.selected_columns, self.localization_layout)
        plotter.plot_localization(mode)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())