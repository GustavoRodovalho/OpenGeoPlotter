import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QTableView, QLabel, QDialog, QLineEdit, QRadioButton, QButtonGroup)
from PyQt5.QtCore import QAbstractTableModel, Qt
from load_csv import LoadCSVDialog

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

        layout = QVBoxLayout()

        self.button = QPushButton("Load CSV")
        self.button.clicked.connect(self.load_csv)
        layout.addWidget(self.button)

        self.table = QTableView()
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            dialog = LoadCSVDialog()
            if dialog.exec_() == QDialog.Accepted:
                sep, header, low_memory = dialog.get_options()
                df = pd.read_csv(file_path, sep=sep, header=header, low_memory=low_memory)
                model = PandasModel(df)
                self.table.setModel(model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WellLoggingViewer()
    viewer.show()
    sys.exit(app.exec_())

# df = pd.read_csv("data/Dataset_unificado_T2.csv", sep=";", low_memory=False)