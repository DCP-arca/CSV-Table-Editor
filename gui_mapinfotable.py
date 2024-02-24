import sys
from PyQt5.QtWidgets import QApplication, QAbstractItemView, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
import re
import webbrowser

STRING_MAPINFO_KEY = ["실제 주소",
                      "다음 맵",
                      "다음 로드뷰",
                      "네이버 맵"]


def is_link(string):
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https:// or ftp://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ipv4
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(url_pattern, string) is not None


class MapInfoTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        self.itemDoubleClicked.connect(self.try_open_link)

        self.clear_table()

    def clear_table(self):
        self.set_mapinfo(["", "", "", ""], [])

    def set_mapinfo(self, datalist, epsg):
        self.epsg = epsg
        self.datalist = datalist
        self.update_table(datalist)

    def update_table(self, datalist):
        self.clear()

        self.setRowCount(5)
        self.setColumnCount(3)

        for index, data in enumerate(datalist):
            if index == 0:
                self.setItem(
                    int(0), 0, QTableWidgetItem(str(STRING_MAPINFO_KEY[index])))
                self.setItem(
                    int(1), 0, QTableWidgetItem(str(data)))
                self.setSpan(0, 0, 1, 3)
                self.setSpan(1, 0, 1, 3)
            else:
                row = int(index + 1)
                self.setItem(
                    row, 0, QTableWidgetItem(str(STRING_MAPINFO_KEY[index])))
                self.setItem(
                    row, 1, QTableWidgetItem(str(data)))
                self.setItem(
                    row, 2, QTableWidgetItem())
                self.setSpan(row, 1, 1, 2)

        noeditable_list = [self.item(2, 1), self.item(3, 1), self.item(4, 1)]
        for target in noeditable_list:
            target.setFlags(target.flags() & ~Qt.ItemIsEditable)

    def try_open_link(self, item):
        content = item.data(Qt.DisplayRole)

        if content and is_link(content):
            webbrowser.open(content)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    table_widget = MapInfoTable()

    table_widget.show()
    sys.exit(app.exec_())
