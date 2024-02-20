import json
import sys
import time

from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QWidget, QTextEdit, QSplitter
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QMessageBox, QDialog, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication
from qt_material import apply_stylesheet

import pandas as pd

from csv_label_adder import CSVLabelAdder
from gui_tableview import TableLayout
from gui_infotable import InfoTable

TITLE_NAME = "CSV Label Adder"
TOP_NAME = "mgj"
APP_NAME = "mgj_csv_label_adder"

WIDTH_RIGHT_LAYOUT = 350


class MyWidget(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_window()
        self.init_content()
        self.main_splitter.setSizes([600, 300])
        self.show()
        self.set_data(pd.read_csv("test_target.csv", encoding="utf8",
                                  sep="|", dtype=object))

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(300, 300)))
        self.resize(self.settings.value("size", QSize(768, 512)))
        self.setAcceptDrops(False)

    def init_content(self):
        main_splitter = QSplitter()
        self.main_splitter = main_splitter
        self.setCentralWidget(main_splitter)

        widget_left = QWidget()
        main_splitter.addWidget(widget_left)
        layout_left = QVBoxLayout()
        widget_left.setLayout(layout_left)

        widget_right = QWidget()
        main_splitter.addWidget(widget_right)
        layout_right = QVBoxLayout()
        widget_right.setLayout(layout_right)

        search_layout = QHBoxLayout()
        layout_left.addLayout(search_layout)

        a = QPushButton("검색창")
        a.setFixedHeight(80)
        search_layout.addWidget(a)

        table_layout = TableLayout(self)
        self.table_layout = table_layout
        table_layout.set_on_clicked(self.on_clicked_table)
        layout_left.addLayout(table_layout)

        info_layout = QHBoxLayout()
        layout_right.addLayout(info_layout, stretch=200000)

        info_table = InfoTable()
        self.info_table = info_table
        info_layout.addWidget(info_table)

        buttons_layout = QVBoxLayout()
        layout_right.addLayout(buttons_layout)

        load_button = QPushButton("불러오기")
        buttons_layout.addWidget(load_button)
        save_button = QPushButton("저장하기")
        buttons_layout.addWidget(save_button)
        export_button = QPushButton("내보내기")
        buttons_layout.addWidget(export_button)

    def set_data(self, data):
        self.data = data
        self.table_layout.setData(data)

    def on_clicked_table(self, item):
        self.info_table.update_table(self.data.iloc[item.row()])

    def closeEvent(self, e):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        e.accept()

    def quit_app(self):
        time.sleep(0.1)
        self.close()
        self.app.closeAllWindows()
        QCoreApplication.exit(0)


if __name__ == '__main__':
    input_list = sys.argv
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_teal_500.xml')
    widget = MyWidget(app)

    time.sleep(0.1)

    sys.exit(app.exec_())
