import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QDialog, QCheckBox, QDialogButtonBox, QGridLayout
from PyQt5.QtWidgets import QApplication, QTableView, QHeaderView, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import QAbstractTableModel, Qt, QTimer
from PyQt5.QtGui import QIntValidator
import pandas as pd

from qt_material import apply_stylesheet

# 페이지만들고 넘기기 만들기
# 표클릭 정렬 만들기
# 선택만들기
# 표클릭후 우클릭 만들기

DIALOG_GRID_WIDTH = 8
DEFAULT_TABLEVIEW_PAGE_SIZE = 20


class ColumnSelectionDialog(QDialog):
    def __init__(self, parent, column_names, current_selected_columns):
        super().__init__(parent)
        self.parent = parent
        self.column_names = column_names
        self.column_checkboxes = []

        self.init_ui(current_selected_columns)

    def init_ui(self, current_selected_columns):
        self.setWindowTitle("Column Selection")

        layout = QGridLayout()

        for index, col in enumerate(self.column_names):
            checkbox = QCheckBox(col)
            if col in current_selected_columns:
                checkbox.setChecked(True)
            self.column_checkboxes.append(checkbox)
            layout.addWidget(checkbox, int(
                index / DIALOG_GRID_WIDTH), index % DIALOG_GRID_WIDTH)

        button_layout = QVBoxLayout()
        layout.addLayout(button_layout, int(
            len(self.column_names) / DIALOG_GRID_WIDTH) + 1, DIALOG_GRID_WIDTH - 1)

        checkbuttons_layout = QHBoxLayout()
        button_layout.addLayout(checkbuttons_layout)
        button_allcheck = QPushButton("모두 선택")
        button_allcheck.pressed.connect(self.check_all)
        checkbuttons_layout.addWidget(button_allcheck)
        button_alluncheck = QPushButton("모두 해제")
        button_alluncheck.pressed.connect(self.uncheck_all)
        checkbuttons_layout.addWidget(button_alluncheck)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_columns(self):
        selected_columns = []
        for checkbox in self.column_checkboxes:
            if checkbox.isChecked():
                selected_columns.append(checkbox.text())
        return selected_columns

    def check_all(self):
        for box in self.column_checkboxes:
            box.setChecked(True)

    def uncheck_all(self):
        for box in self.column_checkboxes:
            box.setChecked(False)


class CSVTableView(QTableView):
    def __init__(self, parent=None, page_size=DEFAULT_TABLEVIEW_PAGE_SIZE):
        super(CSVTableView, self).__init__(parent)
        self.page_size = page_size

    def refresh_tableview_width(self):
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
        self.verticalHeader().resizeSections(QHeaderView.ResizeToContents)

    def set_data(self, data):
        self.model = PandasModel(data, self.page_size)
        self.setModel(self.model)
        self.refresh_tableview_width()

    def get_page(self):
        return self.model._current_page

    def get_maxpage(self):
        model = self.model
        return int(len(model._data) / model._page_size) + 1

    def nextPage(self):
        model = self.model

        if (model._current_page + 1) * model._page_size < len(model._data):
            model._current_page += 1
            self.on_page_change()

    def prevPage(self):
        model = self.model

        if model._current_page > 0:
            model._current_page -= 1
            self.on_page_change()

    def gotoPage(self, page):
        self.model._current_page = page - 1
        self.on_page_change()

    def on_page_change(self):
        self.model.layoutChanged.emit()
        self.verticalHeader().resizeSections(QHeaderView.ResizeToContents)


class PandasModel(QAbstractTableModel):
    def __init__(self, data, page_size):
        super(QAbstractTableModel, self).__init__()
        self._data = data
        self._page_size = page_size
        self._current_page = 0

    def rowCount(self, parent=None):
        return min(self._page_size, len(self._data) - self._current_page * self._page_size)

    def columnCount(self, parent=None):
        return self._data.shape[1] if not self._data.empty else 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            elif orientation == Qt.Vertical:
                return section + 1 + self._page_size * self._current_page
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row() + self._current_page * self._page_size, index.column()])
        return None


class TableLayout(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        upper_button_layout = QHBoxLayout()
        self.addLayout(upper_button_layout)

        self.column_button = QPushButton("라벨선택")
        upper_button_layout.addWidget(self.column_button)
        self.column_button.clicked.connect(self.open_column_selection_dialog)

        self.table_view = CSVTableView()
        self.addWidget(self.table_view)

        self.lower_button_layout = QHBoxLayout()
        self.addLayout(self.lower_button_layout)

        self.prev_button = QPushButton("이전")
        self.prev_button.clicked.connect(self.prevPage)
        self.lower_button_layout.addWidget(self.prev_button, stretch=4)

        self.page_label = QLineEdit("1")
        self.page_label.setAlignment(Qt.AlignLeft)
        self.page_label.setMaximumWidth(60)
        self.page_label.returnPressed.connect(self.gotoPage)
        self.lower_button_layout.addWidget(self.page_label)

        self.maxpage_label = QLabel("/ n")
        self.maxpage_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.lower_button_layout.addWidget(self.maxpage_label, stretch=1)

        self.next_button = QPushButton("다음")
        self.next_button.clicked.connect(self.nextPage)
        self.lower_button_layout.addWidget(self.next_button, stretch=4)

        self.setEnabledUI(False)

    def setData(self, data):
        self.data = data
        self.table_view.set_data(data)
        maxpage = self.table_view.get_maxpage()
        self.maxpage_label.setText("/ " + str(maxpage))
        self.page_label.setValidator(QIntValidator(1, maxpage))
        self.refresh_page()
        self.setEnabledUI(True)

    def open_column_selection_dialog(self):
        current_selected_columns = [self.data.columns[i] for i in range(
            self.data.shape[1]) if not self.table_view.isColumnHidden(i)]
        dialog = ColumnSelectionDialog(
            self.parent, self.data.columns, current_selected_columns)
        if dialog.exec_():
            selected_columns = dialog.get_selected_columns()

            # update_column_selection
            for col in self.data.columns:
                col_index = self.data.columns.get_loc(col)
                self.table_view.setColumnHidden(
                    col_index, col not in selected_columns)

    def gotoPage(self):
        page = int(self.page_label.text())
        if 1 <= page <= self.table_view.get_maxpage():
            self.table_view.gotoPage(page)
        else:
            self.refresh_page()

    def nextPage(self):
        self.table_view.nextPage()
        self.refresh_page()

    def prevPage(self):
        self.table_view.prevPage()
        self.refresh_page()

    def refresh_page(self):
        self.page_label.setText(str(self.table_view.get_page() + 1))

    def setEnabledUI(self, is_disabled):
        targets = [self.page_label, self.prev_button, self.next_button]
        for t in targets:
            t.setEnabled(is_disabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_teal_500.xml')
    window = QMainWindow()
    window.resize(600, 400)

    widget = QWidget()
    window.setCentralWidget(widget)

    table_layout = TableLayout(window)
    widget.setLayout(table_layout)
    table_layout.setData(
        data=pd.read_csv("test_target.csv", encoding="utf8",
                         sep="|", dtype=object))

    window.show()
    sys.exit(app.exec_())
