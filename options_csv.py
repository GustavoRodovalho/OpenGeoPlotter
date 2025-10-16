import sys
import pandas as pd
from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, QLabel, QDialog, QLineEdit, QRadioButton, QComboBox, QTableWidget, QTableWidgetItem)

class LoadCSVDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Specify .csv formats")
        self.setGeometry(200, 200, 300, 100)

        layout = QVBoxLayout()

        self.sep_label = QLabel("Enter the separator character (e.g. , ; \\t |):")
        layout.addWidget(self.sep_label)
        self.input = QLineEdit()
        self.input.setText(";")
        layout.addWidget(self.input)

        self.header_label = QLabel("Header index:")
        layout.addWidget(self.header_label)
        self.header_input = QLineEdit()
        self.header_input.setText("0")
        layout.addWidget(self.header_input)

        self.low_false = QRadioButton("Disable low_memory (set to False)")
        self.low_false.setChecked(True)
        layout.addWidget(self.low_false)

        self.button = QPushButton("OK")
        self.button.clicked.connect(self.accept)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def get_options(self):
        sep = self.input.text()
        sep = "\t" if sep == "\\t" else sep
        header = self.header_input.text()
        header = int(header)
        low_memory = not self.low_false.isChecked() # True if unchecked
        return sep, header, low_memory

class CSVOptions(QDialog):
    def __init__(self, df):
        super().__init__()
        self.setWindowTitle("Set .csv parameters")
        self.setGeometry(200, 200, 300, 400)

        layout = QVBoxLayout()
        self.df = df
        columns = [""] + list(df.columns)

        self.required_fields = {
            "Well ID": QComboBox(),
            "Depth": QComboBox(),
        }
        self.optional_fields = {
            "Latitude": QComboBox(),
            "Longitude": QComboBox(),
            "X": QComboBox(),
            "Y": QComboBox()
        }

        for label_text, combo in self.required_fields.items():
            layout.addWidget(QLabel(label_text))
            combo.addItems(columns[1:])
            layout.addWidget(combo)

        for label_text, combo in self.optional_fields.items():
            layout.addWidget(QLabel(f"{label_text} (optional)"))
            combo.addItems(columns)
            layout.addWidget(combo)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def get_selected_columns(self):
        selected = {label: combo.currentText() for label, combo in self.required_fields.items()}
        selected.update({label: combo.currentText() or None for label, combo in self.optional_fields.items()})
        return selected

class VariableTypeDialog(QDialog):
    def __init__(self, df, selected_columns):
        super().__init__()
        self.setWindowTitle("Set variable types")
        self.setGeometry(200, 200, 500, 600)

        self.df = df
        self.selected_columns = set(col for col in selected_columns.values() if col)
        self.type_map = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select data types for remaining variables:"))

        self.table = QTableWidget()
        remaining_columns = [col for col in df.columns if col not in self.selected_columns]
        self.table.setRowCount(len(remaining_columns))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Variable", "Type"])
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)

        for i, col in enumerate(remaining_columns):
            self.table.setItem(i, 0, QTableWidgetItem(col))

            combo = QComboBox()
            combo.addItems(["int", "float", "str"])
            combo.setCurrentText("float")
            self.table.setCellWidget(i, 1, combo)

        layout.addWidget(self.table)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def get_type_map(self):
        for i in range(self.table.rowCount()):
            col_name = self.table.item(i, 0).text()
            combo = self.table.cellWidget(i, 1)
            self.type_map[col_name] = combo.currentText()
        return self.type_map

