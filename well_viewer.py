import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QTableView, QLabel, QDialog, QTabWidget
from PyQt5.QtCore import QAbstractTableModel, Qt, QPoint
from load_csv import LoadCSVDialog, CSVOptions, VariableTypeDialog

import mplcursors
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import matplotlib.pyplot as plt


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

        # Tab 2: Statistics Plot
        self.plot_tab = QWidget()
        plot_layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        self.plot_tab.setLayout(plot_layout)
        self.tabs.addTab(self.plot_tab, "Variable Statistics")

        # Tab 3: Well Plot
        # ...

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
                        if dtype == "int":
                            self.df[col] = pd.to_numeric(self.df[col], errors="coerce").astype("Int64")
                        elif dtype == "float":
                            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                        elif dtype == "str":
                            self.df[col] = self.df[col].astype(str)
                    except Exception as e:
                        print(f"Could not convert column {col} to {dtype}: {e}")
                print(type_map)

                # Plot statistics in the plot tab
                self.plot_variable_statistics()
    
    def plot_variable_statistics(self):
        if self.df is None:
            return

        self.canvas.figure.clf()
        ax = self.canvas.figure.add_subplot(111)

        numeric_df = self.df.select_dtypes(include=["number"]).dropna()
        melted = numeric_df.melt(var_name="Variable", value_name="Value")

        sns.boxplot(x="Variable", y="Value", data=melted, ax=ax, showfliers=False)
        strip = sns.stripplot(x="Variable", y="Value", data=melted, ax=ax, color="black", alpha=0.3, jitter=True)

        ax.set_title("Variable Statistics")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

        # Add hover tooltips
        mplcursors.cursor(strip.collections, hover=True)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())