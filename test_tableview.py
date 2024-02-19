import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QCheckBox, QPushButton, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class ColumnSelectionDialog(QDialog):
    def __init__(self, parent, column_names, current_selected_columns):
        super().__init__(parent)
        self.parent = parent
        self.column_names = column_names
        self.column_checkboxes = []

        self.init_ui(current_selected_columns)

    def init_ui(self, current_selected_columns):
        self.setWindowTitle("Column Selection")

        layout = QVBoxLayout()

        for col in self.column_names:
            checkbox = QCheckBox(col)
            if col in current_selected_columns:
                checkbox.setChecked(True)
            self.column_checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_columns(self):
        selected_columns = []
        for checkbox in self.column_checkboxes:
            if checkbox.isChecked():
                selected_columns.append(checkbox.text())
        return selected_columns

class DataFrameViewer(QMainWindow):
    def __init__(self, dataframe):
        super().__init__()

        self.df = dataframe
        self.model = QStandardItemModel(self)
        self.table_view = QTableView()
        self.column_button = QPushButton("Column Selection")

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("DataFrame Viewer")

        # Populate the model
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.df.columns)

        for i in range(self.df.shape[0]):
            row = []
            for j in range(self.df.shape[1]):
                item = QStandardItem(str(self.df.iat[i, j]))
                item.setEditable(False)
                row.append(item)
            self.model.appendRow(row)

        # Set the model to the table view
        self.table_view.setModel(self.model)

        # Connect button click to open column selection dialog
        self.column_button.clicked.connect(self.open_column_selection_dialog)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.column_button)
        layout.addWidget(self.table_view)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_column_selection_dialog(self):
        current_selected_columns = [self.df.columns[i] for i in range(self.df.shape[1]) if not self.table_view.isColumnHidden(i)]
        dialog = ColumnSelectionDialog(self, self.df.columns, current_selected_columns)
        if dialog.exec_():
            selected_columns = dialog.get_selected_columns()
            self.update_table_view(selected_columns)

    def update_table_view(self, selected_columns):
        for col in self.df.columns:
            col_index = self.df.columns.get_loc(col)
            self.table_view.setColumnHidden(col_index, col not in selected_columns)

def main():
    app = QApplication(sys.argv)

    # Sample DataFrame
    data = {
        'A': [1, 2, 3, 4],
        'B': [5, 6, 7, 8],
        'C': [9, 10, 11, 12]
    }
    df = pd.DataFrame(data)

    viewer = DataFrameViewer(df)
    viewer.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
