import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QWidget, QTextEdit, QSplitter
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QMessageBox, QDialog, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication
from qt_material import apply_stylesheet

import pandas as pd

from consts import SAVE_KEY_MAP

from data_manager import DataManager
from gui_tableview import CSVTableWidget
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
        self.init_datamanager()
        self.show()

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(300, 300)))
        self.resize(self.settings.value("size", QSize(768, 512)))
        self.setAcceptDrops(True)

    def init_menubar(self):
        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.show_load_dialog)

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
        self.search_widget.on_condition_changed.connect(self.on_condition_changed)
        search_layout.addWidget(self.search_widget)

        table_widget = CSVTableWidget()
        table_widget.on_columnselect_changed.connect(self.on_columnselect_changed)
        self.table_widget = table_widget
        layout_left.addWidget(table_widget)

        info_layout = QVBoxLayout()
        layout_right.addLayout(info_layout, stretch=200000)

        info_table = InfoTable()
        self.info_table = info_table
        self.info_table.set_info_text("아래 불러오기 버튼으로\n파일을 불러오세요!")
        info_layout.addWidget(info_table, stretch=2000)

        mapinfo_table = MapInfoTable()
        mapinfo_table.setFixedHeight(155)
        self.mapinfo_table = mapinfo_table
        info_layout.addWidget(mapinfo_table, stretch=1)

        buttons_layout = QVBoxLayout()
        layout_right.addLayout(buttons_layout)

        load_button = QPushButton("불러오기")
        load_button.pressed.connect(self.show_load_dialog)
        buttons_layout.addWidget(load_button)
        export_button = QPushButton("내보내기")
        export_button.setEnabled(False)
        export_button.pressed.connect(self.show_save_dialog)
        self.export_button = export_button
        buttons_layout.addWidget(export_button)

        self.main_splitter.setSizes([600, 300])

    def init_datamanager(self):
        self.dm = DataManager(self)

    def open_file(self, src):
        if not self.dm.check_parquet_exists(src):
            QMessageBox.information(self, '경고', "처음 불러오는 파일입니다.\n.parquet 파일을 생성합니다.\n이 과정은 오래 걸릴 수 있습니다.")
                
        is_success = self.dm.load(src)
        if not is_success:
            QMessageBox.information(
                self, '경고', "파일을 불러오는데 실패했습니다. 제대로된 파일이 아닌 것 같습니다.")
            return

        self.search_widget.initialize(self.dm.data.columns.to_list())
        self.table_widget.setData(self.dm.cond_data, self.on_clicked_table)
        self.info_table.set_info_text("왼쪽의 테이블을 눌러 자세히 보기!")
        self.export_button.setEnabled(True)

    def show_save_dialog(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "파일을 저장할 곳을 선택해주세요", "", "CSV File (*.csv)")
        if file_path:
            self.dm.export(file_path)

    def show_load_dialog(self):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname = select_dialog.getOpenFileName(
            self, '열 csv 파일을 선택해주세요.', '', 'CSV File(*.csv *.txt)')

        if fname[0]:
            fname = fname[0]
            self.open_file(fname)

    def show_option_dialog(self):
        OptionDialog(self)

    def on_clicked_table(self, cur, prev):
        self.info_table.update_table(self.dm.cond_data.iloc[cur.row()])

        apikey = self.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        pnu = self.dm.data.iloc[cur.row()]["PNU"]

        mapinfolist = ["ERROR", "ERROR", "ERROR", "ERROR"]
        if apikey and pnu:
            result = get_mapinfo_from_pnu(apikey, pnu)
            if result:
                mapinfolist = result

        self.mapinfo_table.update_table(mapinfolist)

    # 필터를 세팅할때 불림 : 필터에 맞춰서 table_widget 내용을 바꿈
    def on_condition_changed(self, conditions):
        self.dm.change_condition(conditions)

        self.table_widget.setData(self.dm.cond_data, self.on_clicked_table)

    def on_columnselect_changed(self, selected_columns):
        self.search_widget.set_columns(selected_columns)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u for u in event.mimeData().urls()]

        if len(files) != 1:
            QMessageBox.information(self, '경고', "파일을 하나만 옮겨주세요.")
            return

        furl = files[0]
        if not furl.isLocalFile():
            QMessageBox.information(self, '경고', "실제 파일을 옮겨주세요.")

        fname = furl.toLocalFile()
        if not fname.endswith(".txt") and not fname.endswith(".csv"):
            QMessageBox.information(self, '경고', "txt나 csv파일만 가능합니다.")
            return

        self.open_file(fname)

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

    # widget.open_file("test_target.csv")

    time.sleep(0.1)

    sys.exit(app.exec_())
