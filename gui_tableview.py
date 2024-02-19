import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView
from PyQt5.QtWidgets import QApplication, QTableView, QHeaderView, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import QAbstractTableModel, Qt, QTimer
import pandas as pd

from qt_material import apply_stylesheet

# 페이지만들고 넘기기 만들기
# 표클릭 정렬 만들기
# 선택만들기
# 표클릭후 우클릭 만들기


class CSVTableView(QTableView):
    def __init__(self, parent=None):
        super(CSVTableView, self).__init__(parent)

    def refresh_tableview_width(self):
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)

    def set_data(self, data):
        self.model = PandasModel(data)
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
            model.layoutChanged.emit()

    def prevPage(self):
        model = self.model

        if model._current_page > 0:
            model._current_page -= 1
            model.layoutChanged.emit()


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(QAbstractTableModel, self).__init__()
        self._data = data
        self._page_size = 10
        self._current_page = 0

    def rowCount(self, parent=None):
        return min(self._page_size, len(self._data) - self._current_page * self._page_size)

    def columnCount(self, parent=None):
        return self._data.shape[1] if not self._data.empty else 0
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row() + self._current_page * self._page_size, index.column()])
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pandas DataFrame을 표로 나타내기")
        self.resize(600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.table_view = CSVTableView()
        self.layout.addWidget(self.table_view)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prevPage)
        self.button_layout.addWidget(self.prev_button, stretch=4)

        self.page_label = QLineEdit("1")
        self.page_label.setAlignment(Qt.AlignLeft)
        self.page_label.setMaximumWidth(60)
        self.button_layout.addWidget(self.page_label)

        self.maxpage_label = QLabel("/ n")
        self.maxpage_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.button_layout.addWidget(self.maxpage_label, stretch=1)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.nextPage)
        self.button_layout.addWidget(self.next_button, stretch=4)

        self.setData(
            data=pd.read_csv("test_target.csv", encoding="utf8",
                             sep="|", dtype=object)[0:25])

    def setData(self, data):
        self.table_view.set_data(data)
        self.maxpage_label.setText("/ " + str(self.table_view.get_maxpage()))
        self.refresh_page()

    def nextPage(self):
        self.table_view.nextPage()
        self.refresh_page()

    def prevPage(self):
        self.table_view.prevPage()
        self.refresh_page()

    def refresh_page(self):
        self.page_label.setText(str(self.table_view.get_page() + 1))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_teal_500.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
