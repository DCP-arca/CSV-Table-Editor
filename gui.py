import sys
import time
import io

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QWidget, QTextEdit, QSplitter
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QMessageBox, QDialog, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication
from qt_material import apply_stylesheet

import pandas as pd
from PIL import Image

from consts import SAVE_KEY_MAP, ENUM_SAVE_COLUMN, ERRORCODE_LOAD, ENUM_TABLEVIEW_INITMODE

from data_manager import DataManager
from gui_tableview import CSVTableWidget
from gui_infotable import InfoTable
from gui_mapinfotable import MapInfoTable
from gui_search import SearchWidget
from gui_dialog import OptionDialog, LoadOptionDialog, SaveOptionDialog, FileIODialog, ImageViewerDialog
from network import get_mapinfo_from_pnu, get_map_img

TITLE_NAME = "CSV Label Adder"
TOP_NAME = "mgj"
APP_NAME = "mgj_csv_label_adder"

WIDTH_RIGHT_LAYOUT = 350

def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    elif  im.mode == "RGBA":
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
        im = im.convert("RGBA")
    # Bild in RGBA konvertieren, falls nicht bereits passiert
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)
    return pixmap

class MyWidget(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_window()
        self.init_menubar()
        self.init_content()
        self.init_variable()
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
        openAction.triggered.connect(self.start_load)

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

        table_widget = CSVTableWidget(self.on_clicked_table)
        table_widget.on_columnselect_changed.connect(
            self.on_columnselect_changed)
        table_widget.on_columnsort_changed.connect(
            self.on_columnsort_changed)
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

        openimg_button = QPushButton("사진열기")
        openimg_button.pressed.connect(self.open_img)
        buttons_layout.addWidget(openimg_button)
        load_button = QPushButton("불러오기")
        load_button.pressed.connect(self.start_load)
        buttons_layout.addWidget(load_button)
        export_button = QPushButton("내보내기")
        export_button.setEnabled(False)
        export_button.pressed.connect(self.show_save_dialog)
        self.export_button = export_button
        buttons_layout.addWidget(export_button)

        self.main_splitter.setSizes([600, 300])

    def init_variable(self):
        self.dm = DataManager(self)
        self.showing_columns = []

    def start_load(self, src=""):
        load_mode = 0
        sep_mode = 0

        if self.dm.data is not None:
            dialog = LoadOptionDialog()
            if dialog.exec_() == QDialog.Accepted:
                load_mode = dialog.selected_radiovalue
                sep_mode = dialog.selected_seperator
            else:
                return

        if src:
            self.load(src, load_mode, sep_mode)
        else:
            self.show_load_dialog(load_mode, sep_mode)

    def load(self, src, load_mode, sep_mode):
        if not self.dm.check_parquet_exists(src):
            QMessageBox.information(
                self, '경고', "처음 불러오는 파일입니다.\n.parquet 파일을 생성합니다.\n이 과정은 오래 걸릴 수 있습니다.")

        error_code = self.dm.load_data(src, load_mode, sep_mode)

        if error_code == ERRORCODE_LOAD.SUCCESS:
            self.showing_columns = self.dm.data.columns.to_list()
            self.search_widget.initialize(self.showing_columns)
            self.table_widget.set_data(
                self.dm.data, ENUM_TABLEVIEW_INITMODE.LOAD)
            self.info_table.set_info_text("왼쪽의 테이블을 눌러 자세히 보기!")
            self.mapinfo_table.clear_table()
            self.export_button.setEnabled(True)
        else:
            error_message = ""
            if error_code == ERRORCODE_LOAD.CANCEL:
                error_message = "취소되었습니다."
            elif error_code == ERRORCODE_LOAD.CSV_FAIL:
                error_message = "CSV파일을 불러오는데 실패했습니다.\n제대로 된 파일이 아닌 것 같습니다."
            elif error_code == ERRORCODE_LOAD.PARQUET_FAIL:
                error_message = "PARQUET파일을 불러오는데 실패했습니다.\n이 에러가 반복되면 .parquet파일을 제거해주세요."
            elif error_code == ERRORCODE_LOAD.NOT_FOUND_PNU:
                error_message = "열 중에 'PNU'가 포함되지 않은 파일이 있습니다."

            QMessageBox.information(self, '불러오기 실패', error_message)

    def open_img(self):
        # 1.epsg 체크
        if not self.mapinfo_table.epsg:
            QMessageBox.information(self, '경고', "행을 하나 선택해주세요.")
            return

        # 2. id / secret 체크
        client_id = self.settings.value(SAVE_KEY_MAP.OPTION_CLIENTID, "")
        client_secret = self.settings.value(SAVE_KEY_MAP.OPTION_CLIENTSECRET, "")
        if not client_id or not client_secret:
            QMessageBox.information(self, '경고', "Naver Cloud Client 값을 설정해주세요.")
            return

        # 3. 이미지 얻어오기, content로 뱉어줌.
        is_success, content = get_map_img(client_id, client_secret, self.mapinfo_table.epsg)
        if not is_success:
            QMessageBox.information(self, '경고', "Naver Cloud에 접속하는데 실패했습니다.\n\n"+str(content))
            return

        # 4. image_data -> pixmap 전환
        try:
            image_data = io.BytesIO(content)
            image = Image.open(image_data)
            pixmap = pil2pixmap(image)

        except Exception as e:
            QMessageBox.information(self, '경고', "이미지를 변환하는데 실패했습니다.\n\n"+str(e))
            
        ImageViewerDialog(pixmap).exec_()
        
    def show_save_dialog(self):
        dialog = SaveOptionDialog()
        if dialog.exec_():
            list_value = dialog.list_selected_value
            sep_mode = list_value[0]
            list_target_column = self.showing_columns if list_value[
                1] == ENUM_SAVE_COLUMN.SELECTED else None
            select_mode = list_value[2]
            file_path, _ = QFileDialog.getSaveFileName(
                self, "파일을 저장할 곳을 선택해주세요", "", "CSV File (*.csv)")
            if file_path:
                self.dm.export(file_path,
                               sep_mode=sep_mode,
                               list_target_column=list_target_column,
                               select_mode=select_mode)

    def show_load_dialog(self, load_mode, sep_mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname = select_dialog.getOpenFileName(
            self, '열 csv 파일을 선택해주세요.', '', 'CSV File(*.csv *.txt)')

        if fname[0]:
            fname = fname[0]
            self.load(fname, load_mode, sep_mode)

    def show_option_dialog(self):
        OptionDialog(self)

    def on_clicked_table(self, cur, prev):
        # 표시할 행을 구함
        target_index = cur.row() + (self.table_widget.get_page() - 1) * \
            self.table_widget.page_size
        target_df = self.dm.cond_data.iloc[target_index]

        # 1. info table 업데이트
        self.info_table.update_table(target_df)

        # 2. mapinfo table 업데이트
        # 2.1. apikey, pnu 구함, 못구하면 둘다 공백이 나옴
        apikey = self.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        pnu = target_df["PNU"] if "PNU" in target_df else ""

        # 2.2. mapinfolist 구함
        mapinfolist = ["ERROR", "ERROR", "ERROR", "ERROR"]
        if apikey and pnu:
            mapinfo, epsg = get_mapinfo_from_pnu(apikey, pnu)
            if mapinfo:
                mapinfolist = mapinfo
        self.mapinfo_table.set_mapinfo(mapinfolist, epsg)

    # 검색필터를 세팅할때 호출됨 : 필터에 맞춰서 table_widget 내용을 바꿈
    def on_condition_changed(self, conditions):
        self.dm.change_condition(conditions)

        self.table_widget.set_data(
            self.dm.cond_data, ENUM_TABLEVIEW_INITMODE.CONDITION)

    # 라벨을 세팅할때 호출됨 : 세팅된 것에 맞춰 검색필터를 제한함.
    def on_columnselect_changed(self, selected_columns):
        self.showing_columns = selected_columns
        self.search_widget.set_columns(selected_columns)

    def on_columnsort_changed(self, column_name, sort_mode):
        FileIODialog(
            "정렬 중입니다.(파일이 크면 오래 걸릴 수 있습니다.)",
            lambda: self.dm.sort(column_name, sort_mode)).exec_()

        self.table_widget.set_data(self.dm.data, ENUM_TABLEVIEW_INITMODE.SORT)

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

        self.start_load(fname)

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

    widget.load("target.csv", 0, 0)

    time.sleep(0.1)

    sys.exit(app.exec_())
