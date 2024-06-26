import sys
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QDialog
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication

from consts import SAVE_KEY_MAP, ENUM_SAVE_COLUMN, ENUM_SAVE_ROW, ERRORCODE_LOAD, ENUM_TABLEVIEW_INITMODE, ENUM_TABLEVIEW_HVFUNC

from data_manager import DataManager, DataEditType
from gui_tableview import CSVTableWidget
from gui_infotable import InfoTable
from gui_mapinfotable import MapInfoTable
from gui_search import SearchWidget
from gui_dialog import OptionDialog, LoadOptionDialog, SaveOptionDialog, ImageViewerDialog, FuncLoadingDialog, CoordDialog, SimpleInputDialog
from network import get_mapinfo_from_pnu
from clipboard import clipboard_copy_csvte_info, clipboard_paste_csvte_info
from theme import apply_theme
from gui_apitable import APIInfoLayout

TITLE_NAME = "CSV Table Editor"
TOP_NAME = "mgj"
APP_NAME = "mgj_csv_label_adder"

WIDTH_RIGHT_LAYOUT = 350


def strtobool(val):
    if isinstance(val, bool):
        return val

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def find_pnu_from_df(df):
    search_table = ['PNU', 'pnu']

    pnu = ''
    for tag in search_table:
        if tag in df:
            pnu = df[tag]

    if not pnu:
        for x in df:
            target = x
            if target:
                if not isinstance(target, str):
                    try:
                        target = str(target)
                    except Exception as e:
                        print("find_pnu_from_df : error while converting to str", e)
                        continue

                if len(target) == 19 and target.isdigit():
                    pnu = target
                    break

    return pnu


class CSVTableEditor(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_window()  # 기본설정
        self.init_menubar()  # 메뉴바 생성
        self.init_content()  # 내용물 생성
        self.init_variable()  # 멤버변수 생성
        apply_theme(app, self.settings.value(
            SAVE_KEY_MAP.OPTION_FONTSIZE, 13))  # 테마적용
        self.show()

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        # settings.value(key, defaultvalue)
        self.move(self.settings.value("pos", QPoint(300, 300)))
        self.resize(self.settings.value("size", QSize(768, 512)))
        self.setAcceptDrops(True)  # 메인 윈도우에 드래그드랍을 허용함

    def init_menubar(self):
        # 메뉴바 생성
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&파일')

        openAction = QAction('파일 열기(Open file)', self)
        openAction.setShortcut('Ctrl+O')
        # action 안에 triggered라고 하는 callback(이벤트성 함수)가 있고 거기에 내 함수를 묶음.
        openAction.triggered.connect(self.start_load)

        coordAction = QAction('좌표로 찾기(Find by Coord)', self)
        coordAction.setShortcut('Ctrl+P')
        coordAction.triggered.connect(self.show_coord_dialog)

        optionAction = QAction('옵션(Option)', self)
        optionAction.setShortcut('Ctrl+U')
        optionAction.triggered.connect(self.show_option_dialog)

        exitAction = QAction('종료(Exit)', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.quit_app)

        filemenu.addAction(openAction)
        filemenu.addAction(coordAction)
        filemenu.addAction(optionAction)
        filemenu.addAction(exitAction)

    def init_content(self):
        # 최상단에 스플리터 있음.
        main_splitter = QSplitter()
        self.main_splitter = main_splitter
        self.setCentralWidget(main_splitter)  # 스플리터를 메인 위젯으로 설정

        # 왼쪽 레이아웃
        widget_left = QWidget()  # 빈 위젯
        main_splitter.addWidget(widget_left)
        layout_left = QVBoxLayout()  # Vertical Box Layout
        widget_left.setLayout(layout_left)

        # 오른쪽 레이아웃
        widget_right = QWidget()
        main_splitter.addWidget(widget_right)
        layout_right = QVBoxLayout()
        widget_right.setLayout(layout_right)

        # 1. 서치 위젯
        search_layout = QHBoxLayout()
        layout_left.addLayout(search_layout)

        self.search_widget = SearchWidget()
        self.search_widget.setFixedHeight(70)  # 70 px 고정 높이를 가짐
        self.search_widget.on_condition_changed.connect(  # on_condition_changed 콜백에 내 함수를 묶음
            self.on_condition_changed)
        search_layout.addWidget(self.search_widget)

        # 2. 테이블 위젯
        table_widget = CSVTableWidget(
            self,
            self.on_clicked_table,
            self.on_value_edit_callback,
            self.on_hv_edit_callback,
            self.settings.value(SAVE_KEY_MAP.OPTION_TABLEPAGESIZE, 20),
            strtobool(self.settings.value(
                SAVE_KEY_MAP.OPTION_LOWSPECMODE, "False")),
        )
        # 3개의 콜백 묶음
        table_widget.on_page_refreshed.connect(self.on_page_refreshed)
        table_widget.on_columnselect_changed.connect(
            self.on_columnselect_changed)
        table_widget.on_columnsort_asked.connect(
            self.on_columnsort_asked)
        # 나중에 써먹어야하니까 self. 으로 내부 변수로 만듬
        self.table_widget = table_widget
        layout_left.addWidget(table_widget)

        # 3. 인포 테이블
        info_layout = QVBoxLayout()
        layout_right.addLayout(info_layout, stretch=200000)

        info_table = InfoTable()
        self.info_table = info_table
        self.info_table.set_info_text("아래 불러오기 버튼으로\n파일을 불러오세요!")
        info_layout.addWidget(info_table, stretch=1)

        # 4. 맵인포 테이블
        mapinfo_table = MapInfoTable()
        self.mapinfo_table = mapinfo_table
        info_layout.addWidget(mapinfo_table)

        # API Type Selection
        api_info_layout = APIInfoLayout(self)
        self.api_info_layout = api_info_layout
        info_layout.addLayout(api_info_layout)

        # 5. buttons_layout
        buttons_layout = QVBoxLayout()
        layout_right.addLayout(buttons_layout)

        openimg_button = QPushButton("사진열기")  # 첫인자가 텍스트임.
        openimg_button.clicked.connect(self.open_img)  # clicked 콜백에 함수를 묶고 있음.
        openimg_button.setEnabled(False)  # 처음 실행시에는 꺼놓음.
        self.openimg_button = openimg_button
        buttons_layout.addWidget(openimg_button)
        load_button = QPushButton("불러오기")
        load_button.clicked.connect(self.start_load)
        buttons_layout.addWidget(load_button)
        export_button = QPushButton("내보내기")
        export_button.setEnabled(False)
        export_button.clicked.connect(self.show_save_dialog)
        self.export_button = export_button
        buttons_layout.addWidget(export_button)

        self.main_splitter.setSizes([600, 300])

    def init_variable(self):
        self.dm = DataManager(self)
        self.showing_columns = []
        self.hv_copy_mode = False

    def start_load(self, src=""):
        load_mode = 0
        # sep_mode = 0

        dialog = LoadOptionDialog(self.dm.is_already_loaded())
        if dialog.exec_() == QDialog.Accepted:
            load_mode = dialog.selected_radiovalue
            # sep_mode = dialog.selected_seperator
        else:
            return

        if src:
            self.load(src, load_mode)
        else:
            self.show_load_dialog(load_mode)

    def load(self, src, load_mode):
        if not self.dm.check_parquet_exists(src):
            QMessageBox.information(
                self, '경고', "처음 불러오는 파일입니다.\n.parquet 파일을 생성합니다.\n이 과정은 오래 걸릴 수 있습니다.")

        error_code = self.dm.load_data(src, load_mode)

        if error_code == ERRORCODE_LOAD.SUCCESS:
            self.hv_copy_mode = False
            self.showing_columns = self.dm.cond_data.columns.to_list()
            self.search_widget.initialize(self.showing_columns)
            self.table_widget.set_data(
                self.dm.cond_data, ENUM_TABLEVIEW_INITMODE.LOAD)
            if strtobool(self.settings.value(SAVE_KEY_MAP.OPTION_LOWSPECMODE, "False")):
                self.info_table.set_info_text("저사양 모드 실행중\n(표 숨겨짐)")
            else:
                self.info_table.set_info_text("왼쪽의 테이블을 눌러 자세히 보기!")
            self.search_widget.set_info_text("왼쪽의 버튼을 눌러 필터를 추가!")
            self.mapinfo_table.clear_table()
            self.api_info_layout.clear()
            self.export_button.setEnabled(True)
            self.openimg_button.setEnabled(True)
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
            elif error_code == ERRORCODE_LOAD.NOT_FOUND_SEP:
                error_message = "CSV 파일 내부에 |나 ,가 없습니다.\n잘못된 파일인 것 같습니다."

            QMessageBox.information(self, '불러오기 실패', error_message)

    def open_img(self, info_dict={}):
        if not info_dict:
            if not self.mapinfo_table.epsg:
                QMessageBox.information(self, '경고', "주소를 확인할 수 없습니다.")
                return
            info_dict = {
                "addr": self.mapinfo_table.datalist[0],
                "epsg": self.mapinfo_table.epsg
            }

        addr = info_dict["addr"]
        epsg = self.mapinfo_table.epsg if not info_dict else info_dict['epsg']

        ImageViewerDialog(self, addr, epsg).show()

    def show_save_dialog(self):
        dialog = SaveOptionDialog()
        if dialog.exec_() == QDialog.Accepted:  # 꺼질때까지 스턱
            list_value = dialog.list_selected_value
            sep_mode = list_value[0]
            list_target_column = self.showing_columns if list_value[
                1] == ENUM_SAVE_COLUMN.SELECTED else None
            select_mode = list_value[2]
            file_path, _ = QFileDialog.getSaveFileName(
                self, "파일을 저장할 곳을 선택해주세요", "",
                # "DBF File (*.dbf)" if self.dm.is_dbf_loaded else "CSV File (*.csv)") #TODO dbf load
                "CSV File (*.csv)")
            if file_path:
                # 내보내기 전, 체크 확인, 체크 모드라면 df자체를 담아서 보냄.
                list_checked = []
                if select_mode == ENUM_SAVE_ROW.CHECKED or select_mode == ENUM_SAVE_ROW.CHECKED_SELECT:
                    if not self.table_widget.list_check:
                        QMessageBox.information(
                            self, '경고', "내보낼 체크가 안되어있습니다.")
                        return
                    page_seed = (self.table_widget.get_page() -
                                 1) * self.table_widget.page_size
                    for index in self.table_widget.list_check:
                        list_checked.append(index + page_seed)

                # 내보내기
                is_export_success = self.dm.export(file_path,
                                                   sep_mode=sep_mode,
                                                   list_target_column=list_target_column,
                                                   select_mode=select_mode,
                                                   list_checked=list_checked)
                if not is_export_success:
                    QMessageBox.information(
                        self, '경고', "내보내는 중에 에러가 발생했습니다.")

    def show_load_dialog(self, load_mode):
        select_dialog = QFileDialog()
        select_dialog.setFileMode(QFileDialog.ExistingFile)
        fname = select_dialog.getOpenFileName(   # 여기서 dialog가 꺼질때까지 스턱되어있음. dialog가 성공적으로 파일을 고르면, fname으로 고른 파일의 경로가 들어온다.
            self, '열 csv 파일을 선택해주세요.', '', 'CSV File(*.csv *.txt *.dbf)')

        if fname[0]:  # 우리는 하나만 고르는 모드이므로, 첫번째 값이 그것임. dialog가 취소하면 fname == []
            fname = fname[0]
            self.load(fname, load_mode)

    def show_coord_dialog(self):
        CoordDialog(self).show()

    def show_option_dialog(self):
        OptionDialog(self).exec_()

    # 표의 행을 눌렀을때 호출됨
    def on_clicked_table(self, cur, prev):
        self.refresh_tables(cur.row())

    def refresh_tables(self, row):
        # 표시할 행을 구함
        target_index = row + (self.table_widget.get_page() - 1) * \
            self.table_widget.page_size
        target_df = self.dm.cond_data.iloc[target_index]

        # 1. info table 업데이트
        self.info_table.update_table(target_df)

        # 2. mapinfo table 업데이트
        # 2.1. apikey, pnu 구함, 못구하면 둘다 공백이 나옴
        apikey = self.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        pnu = find_pnu_from_df(target_df)

        # 2.2. mapinfolist 구함
        mapinfolist = ["ERROR", "ERROR", "ERROR", "ERROR"]
        epsglist = []
        if apikey and pnu:
            m, e = get_mapinfo_from_pnu(apikey, pnu)
            if m and e:
                mapinfolist = m
                epsglist = e
        self.mapinfo_table.set_mapinfo(mapinfolist, epsglist)

        # 3. api_info_layout
        if pnu:
            self.api_info_layout.set_pnu(pnu)

    def on_value_edit_callback(self, row, col, value):
        target_index = row + (self.table_widget.get_page() - 1) * \
            self.table_widget.page_size

        self.dm.change_value(target_index, col, value)

        self.refresh_tables(row)

    def on_hv_edit_callback(self, is_column, row, str_menu):
        pos = row
        if not is_column:
            pos = pos + (self.table_widget.get_page() - 1) * \
                self.table_widget.page_size

        if str_menu == ENUM_TABLEVIEW_HVFUNC.COPY:
            clipboard_copy_csvte_info(self.dm.cond_data, pos, is_column)
            self.hv_copy_mode = True
        else:
            edit_type = None
            args = None
            if str_menu == ENUM_TABLEVIEW_HVFUNC.CREATE:
                if is_column:
                    dialog = SimpleInputDialog(
                        self, '이름 설정', '새 열의 이름을 설정하세요.')
                    if dialog.exec_() == QDialog.Accepted:
                        title = dialog.getText()
                        if title:
                            edit_type = DataEditType.ADD_COLUMN
                            args = [pos, title]
                else:
                    edit_type = DataEditType.ADD_ROW
                    args = [pos]
            elif str_menu == ENUM_TABLEVIEW_HVFUNC.DUPLICATE:
                edit_type = DataEditType.DUPLICATE_COLUMN if is_column else DataEditType.DUPLICATE_ROW
                args = [pos]
            elif str_menu == ENUM_TABLEVIEW_HVFUNC.REMOVE:
                rows, columns = self.dm.cond_data.shape
                if is_column:
                    if columns <= 1:
                        QMessageBox.information(self, '경고', "열의 갯수가 너무 적습니다.")
                        return
                    edit_type = DataEditType.REMOVE_COLUMN
                else:
                    if rows <= 1:
                        QMessageBox.information(self, '경고', "행의 갯수가 너무 적습니다.")
                        return
                    edit_type = DataEditType.REMOVE_ROW
                args = [pos]
            elif str_menu == ENUM_TABLEVIEW_HVFUNC.PASTE:
                target_h, result = clipboard_paste_csvte_info()
                if target_h != is_column:
                    QMessageBox.information(self, '경고', "붙여넣을 행이나 열이 잘못되었습니다.")
                    return
                if not self.hv_copy_mode:
                    QMessageBox.information(self, '경고', "복사를 먼저 진행해주세요.")
                    return

                edit_type = DataEditType.EDIT_COLUMN if is_column else DataEditType.EDIT_ROW
                args = [pos, result]

            if edit_type:
                self.dm.change_hv(edit_type, args)
                self.table_widget.set_data(
                    self.dm.cond_data, ENUM_TABLEVIEW_INITMODE.EDIT)

                if edit_type == DataEditType.REMOVE_ROW or edit_type == DataEditType.REMOVE_COLUMN:
                    self.refresh_tables(row - 1)
                else:
                    self.refresh_tables(row)

                if not str_menu == ENUM_TABLEVIEW_HVFUNC.PASTE:
                    self.hv_copy_mode = False

    # 검색필터를 세팅할때 호출됨 : 필터에 맞춰서 table_widget 내용을 바꿈
    def on_condition_changed(self, conditions):
        is_success = self.dm.change_condition(conditions)
        if not is_success:
            QMessageBox.information(self, '경고', "조건식이 숫자가 아니거나 잘못되었습니다.")

            self.search_widget.on_edit_failed(self.dm.now_conditions)
            return

        self.table_widget.set_data(
            self.dm.cond_data, ENUM_TABLEVIEW_INITMODE.CONDITION)

    # 페이지가 새로고침될때 호출됨 (언제 호출되는지는 tableview.refresh_page 참조)
    def on_page_refreshed(self):
        self.info_table.set_info_text("왼쪽의 테이블을 눌러 자세히 보기!")

    # 라벨을 세팅할때 호출됨 : 세팅된 것에 맞춰 검색필터를 제한함.
    def on_columnselect_changed(self, selected_columns):
        self.showing_columns = selected_columns
        self.search_widget.set_columns(selected_columns)

    # 정렬이 실행될때 호출됨
    def on_columnsort_asked(self, index, column_name, sort_mode):
        dialog = FuncLoadingDialog(
            "정렬 중입니다.(파일이 크면 오래 걸릴 수 있습니다.)",
            lambda: self.dm.sort(column_name, sort_mode))

        if dialog.exec_() == QDialog.Accepted:
            is_success = dialog.result
            if is_success:
                self.table_widget.set_data(
                    self.dm.cond_data, ENUM_TABLEVIEW_INITMODE.SORT)
                self.table_widget.on_columnsort_answered(
                    index, column_name, sort_mode)
                return

        QMessageBox.information(self, '경고', "숫자로 이루어진 경우에만 정렬이 가능합니다.")

    # 드래그드랍 이벤트를 위한 고정 템플릿
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
        if not fname.endswith(".txt") and not fname.endswith(".csv") and not fname.endswith(".dbf"):
            QMessageBox.information(self, '경고', "txt나 csv, dbf파일만 가능합니다.")
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
    app = QApplication(sys.argv)  # 어플리케이션 실행
    window = CSVTableEditor(app)  # 내 위젯 실행되고 스턱.
    sys.exit(app.exec_())  # 어플리케이션 종료
