import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView
from PyQt5.QtWidgets import QApplication, QTableView, QHeaderView, QSizePolicy, QWidget, QVBoxLayout
from PyQt5.QtCore import QAbstractTableModel, Qt, QTimer
import pandas as pd



#페이지만들고 넘기기 만들기
#표클릭 정렬 만들기
#선택만들기
#표클릭후 우클릭 만들기



# class CustomTableView(QTableView):
#     def __init__(self, parent=None):
#         super(CustomTableView, self).__init__(parent)
#         self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
#         self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         self.verticalHeader().setVisible(False)

#     def sizeHintForColumn(self, column):
#         return self.horizontalHeader().sectionSize(column)


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None


class MainWindow(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Pandas DataFrame을 표로 나타내기")
        self.resize(600, 400)

        self.table_view = QTableView()
        # self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.setModel(PandasModel(data))
        self.table_view.resizeColumnsToContents()

        self.setCentralWidget(self.table_view)

        QTimer.singleShot(2000, self.refresh_tableview_width)

    def refresh_tableview_width(self):  # 이거 버튼으로 만들기
        self.table_view.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)


def main():
    # 샘플 데이터 생성
    data = pd.read_csv("test_target.csv", encoding="utf8",
                       sep="|", dtype=object)

    # PyQt5 어플리케이션 시작
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
