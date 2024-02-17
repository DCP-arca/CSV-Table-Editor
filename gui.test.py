import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

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
        self.table_view.setModel( PandasModel(data))

        self.setCentralWidget(self.table_view)

def main():
    # 샘플 데이터 생성
    data = pd.DataFrame({'이름': ['Alice', 'Bob', 'Charlie'],
                         '나이': [25, 30, 35],
                         '직업': ['학생', '개발자', '디자이너']})

    # PyQt5 어플리케이션 시작
    app = QApplication(sys.argv)
    window = MainWindow(data)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()