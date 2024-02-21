import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont


class InfoTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        self.placeholder_text = ""

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.model() is not None and self.model().rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.save()
        col = self.palette().placeholderText().color()
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
        self.placeholder_text = text

    def update_table(self, dataframes):
        self.clear()

        self.setRowCount(int(len(dataframes) / 2))
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

    table_widget = InfoTable()
    # table_widget.update_table(dataframes)

    table_widget.show()
    sys.exit(app.exec_())
