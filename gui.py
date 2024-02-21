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
from gui_tableview import TableWidget
from gui_infotable import InfoTable
from gui_mapinfotable import MapInfoTable
from gui_search import SearchWidget
from gui_dialog import OptionDialog
from get_mapinfo_from_pnu import get_mapinfo_from_pnu

TITLE_NAME = "CSV Label Adder"
TOP_NAME = "mgj"
APP_NAME = "mgj_csv_label_adder"

WIDTH_RIGHT_LAYOUT = 350


class MyWidget(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_window()
        self.init_menubar()
        self.init_content()
        self.main_splitter.setSizes([600, 300])
        self.show()

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(300, 300)))
        self.resize(self.settings.value("size", QSize(768, 512)))
        self.setAcceptDrops(False)

    def init_menubar(self):
        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.show_file_dialog)

        optionAction = QAction('옵션(Option)', self)
        optionAction.setShortcut('Ctrl+U')
        optionAction.triggered.connect(self.show_option_dialog)

        exitAction = QAction('종료(Exit)', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.quit_app)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openAction)
        filemenu.addAction(optionAction)
        filemenu.addAction(exitAction)

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

        self.search_widget = SearchWidget()
        self.search_widget.setFixedHeight(70)
        self.search_widget.on_condition_changed.connect(
            self.on_condition_changed)
        search_layout.addWidget(self.search_widget)

        table_widget = TableWidget()
        self.table_widget = table_widget
        layout_left.addWidget(table_widget)

        info_layout = QVBoxLayout()
        layout_right.addLayout(info_layout, stretch=200000)

        info_table = InfoTable()
        self.info_table = info_table
        self.set_info_text("PLEASE_LOAD_FILE")
        info_layout.addWidget(info_table, stretch=2000)

        mapinfo_table = MapInfoTable()
        mapinfo_table.setFixedHeight(155)
        self.mapinfo_table = mapinfo_table
        info_layout.addWidget(mapinfo_table, stretch=1)

        buttons_layout = QVBoxLayout()
        layout_right.addLayout(buttons_layout)

        load_button = QPushButton("불러오기")
        load_button.pressed.connect(self.show_file_dialog)
        buttons_layout.addWidget(load_button)
        save_button = QPushButton("저장하기")
        buttons_layout.addWidget(save_button)
        export_button = QPushButton("내보내기")
        buttons_layout.addWidget(export_button)

    def set_data(self, data):
        self.data = data
        self.search_widget.initialize(self.data.columns.to_list())

        self.cond_data = data.copy(deep=True)
        self.table_widget.setData(self.cond_data, self.on_clicked_table)

    def set_info_text(self, key):
        value = ""

        if key == "PLEASE_LOAD_FILE":
            value = "아래 불러오기 버튼으로\n파일을 불러오세요!"
        elif key == "PLEASE_CLICK_LEFT":
            value = "왼쪽의 테이블을 눌러 자세히 보기!"

        self.info_table.set_info_text(value)

    def open_file(self, src):
        self.set_data(pd.read_csv(
            src, encoding="utf8", sep="|", dtype=object))
        self.set_info_text("PLEASE_CLICK_LEFT")

    def show_file_dialog(self):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname = select_dialog.getOpenFileName(
            self, '열 csv 파일을 선택해주세요.', '', 'CSV File(*.csv)')

        if fname[0]:
            fname = fname[0]
            self.open_file(fname)

    def show_option_dialog(self):
        OptionDialog(self)

    def on_clicked_table(self, cur, prev):
        self.info_table.update_table(self.cond_data.iloc[cur.row()])

        apikey = self.settings.value("option_apikey", "")
        pnu = self.data.iloc[cur.row()]["PNU"]

        mapinfolist = ["ERROR", "ERROR", "ERROR", "ERROR"]
        if apikey and pnu:
            result = get_mapinfo_from_pnu(apikey, pnu)
            if result:
                mapinfolist = result

        self.mapinfo_table.update_table(mapinfolist)

    def on_condition_changed(self, conditions):
        self.cond_data = self.data.copy(deep=True)

        for cond in conditions:
            cl = cond.split()
            min_val = cl[0]
            column_name = cl[2]
            max_val = cl[4]
            self.cond_data = self.cond_data[(self.cond_data[column_name] >= min_val) &
                                            (self.cond_data[column_name] <= max_val)]

        self.table_widget.setData(self.cond_data, self.on_clicked_table)

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

    widget.open_file("test_target.csv")

    time.sleep(0.1)

    sys.exit(app.exec_())
