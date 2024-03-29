import sys
import math
from PyQt5.QtWidgets import QApplication, QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont, QColor


class InfoTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.placeholder_text = ""

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.model() is not None and self.model().rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.save()
        col = QColor("#009688")  # self.palette().placeholderText().color()
        painter.setPen(col)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        painter.setFont(font)
        fm = self.fontMetrics()
        elided_text = fm.elidedText(
            self.placeholder_text, Qt.ElideRight, self.viewport().width()
        )
        painter.drawText(self.viewport().rect(),
                         Qt.AlignCenter, elided_text)
        painter.restore()

    def set_info_text(self, text):
        m = self.model()
        m.removeRows(0, m.rowCount())
        m.removeColumns(0, m.columnCount())
        self.placeholder_text = text

    def update_table(self, dataframes):
        self.clear()

        self.setRowCount(math.ceil(len(dataframes) / 2))
        self.setColumnCount(4)

        row = 0
        col = 0
        for key, value in dataframes.items():
            self.setItem(
                int(row), (col % 2) * 2, QTableWidgetItem(str(key)))
            self.setItem(
                int(row), (col % 2) * 2 + 1, QTableWidgetItem(str(value)))
            row += 0.5
            col += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)

    import pandas as pd
    table_widget = InfoTable()

    dataframes = pd.read_csv(
        "test.csv", encoding="euc-kr", sep="|", dtype=object)
    table_widget.update_table(dataframes.iloc[0])

    table_widget.show()
    sys.exit(app.exec_())
