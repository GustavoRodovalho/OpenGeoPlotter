import sys
import pandas as pd
from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, QLabel, QDialog, QLineEdit, QRadioButton)

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