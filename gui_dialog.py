import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMessageBox, QSlider, QComboBox, QHBoxLayout, QVBoxLayout, QGroupBox, QCheckBox, QRadioButton, QDialogButtonBox, QFileDialog, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent, QPoint, QSize, QTimer
from PyQt5.QtGui import QIntValidator, QPixmap
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from consts import SAVE_KEY_MAP, ENUM_LOAD_MODE, ENUM_SEPERATOR, CONST_COORDSYS_STRMAP, ENUM_STATICMAP_BASEMAP
from network import get_addr_from_epsg, get_map_img


def transform_to_epsg4326(x, y, epsg):
    if epsg == 4326:
        return x, y

    # 좌표를 GeoDataFrame으로 변환
    gdf = gpd.GeoDataFrame(
        geometry=[Point(y, x)], crs=f"EPSG:{epsg}")

    # EPSG:4326으로 변환
    gdf = gdf.to_crs(epsg=4326)
    p = gdf.loc[0][0]

    return float(p.x), float(p.y)


# 주의! 이 txt 순서는 ENUM_SEPERATOR, ENUM_SAVE_COLUMN, ENUM_SAVE_ROW에 영향을 받습니다.
LIST_GROUPBOX_TEXT = [
    ["열 분리자 선택", ["| (버티컬바)", ", (쉼표)"]],
    ["열 내보내기", ["모두", "현재 보이는 열(라벨)만 내보내기"]],
    ["행 내보내기", ["모두",
                "불러와진 행만 내보내기",
                "불러와진 행에 select열 추가해 내보내기",
                # "체크된 행만 내보내기", ##TODO: possible error
                # "체크된 행에 select열 추가해 내보내기" ##TODO: possible error
                ]]
]


def create_empty(minimum_width=0, minimum_height=0):
    w = QWidget()
    w.setMinimumWidth(minimum_width)
    w.setMinimumHeight(minimum_height)
    return w


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


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


class OptionDialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle('옵션')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.resize(400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        vbox_key = QVBoxLayout()
        layout.addLayout(vbox_key)

        def create_lineedit_key(title, placeholder, savekey):
            label = QLabel(title)
            vbox_key.addWidget(label)
            lineedit = QLineEdit(self)
            lineedit.setPlaceholderText(placeholder)
            lineedit.setText(self.parent.settings.value(savekey, ""))
            vbox_key.addWidget(lineedit)
            return lineedit

        self.le_apikey = create_lineedit_key(
            'VWorld API 키 입력:', "API 키를 입력해주세요.", SAVE_KEY_MAP.OPTION_APIKEY)

        layout.addStretch(1)

        layout.addWidget(create_empty(minimum_height=10))

        hbox_font = QHBoxLayout()
        layout.addLayout(hbox_font)
        hbox_font.addWidget(QLabel("글꼴 크기 : "))
        lineedit_font = QLineEdit(self)
        lineedit_font.setPlaceholderText("13")
        lineedit_font.setText(str(self.parent.settings.value(
            SAVE_KEY_MAP.OPTION_FONTSIZE, 13)))
        lineedit_font.setValidator(QIntValidator(1, 30))
        self.lineedit_font = lineedit_font
        hbox_font.addWidget(lineedit_font)

        hbox_page = QHBoxLayout()
        layout.addLayout(hbox_page)
        hbox_page.addWidget(QLabel("한 페이지에 불러올 행의 갯수 : "))
        lineedit_page = QLineEdit(self)
        lineedit_page.setPlaceholderText("20")
        lineedit_page.setText(str(self.parent.settings.value(
            SAVE_KEY_MAP.OPTION_TABLEPAGESIZE, 20)))
        lineedit_page.setValidator(QIntValidator(1, 1000))
        self.lineedit_page = lineedit_page
        hbox_page.addWidget(lineedit_page)
        layout.addWidget(QLabel("*주의 : 행의 갯수가 너무 많은 경우 렉이 발생합니다"))

        layout.addStretch(1)

        hbox_lowspec = QHBoxLayout()
        layout.addLayout(hbox_lowspec)
        hbox_lowspec.addWidget(QLabel("저사양 모드 : "))
        checkbox_lowspec = QCheckBox()
        checkbox_lowspec.setChecked(strtobool(self.parent.settings.value(
            SAVE_KEY_MAP.OPTION_LOWSPECMODE, "False")))
        self.checkbox_lowspec = checkbox_lowspec
        hbox_lowspec.addWidget(checkbox_lowspec)

        layout.addWidget(QLabel("*글꼴 크기, 행 갯수, 저사양 모드는 다음 실행부터 적용됩니다."))

        button_close = QPushButton("저장 및 닫기")
        button_close.clicked.connect(self.on_click_close_button)
        self.button_close = button_close
        layout.addWidget(button_close)

    def on_click_select_button(self, code):
        select_dialog = QFileDialog()
        save_loc = select_dialog.getExistingDirectory(
            self, '저장할 위치를 골라주세요.')

        if save_loc:
            self.parent.change_path(code, save_loc)

            self.refresh_label(code)

    def on_click_close_button(self):
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_APIKEY, self.le_apikey.text())
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_FONTSIZE, int(self.lineedit_font.text()))
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_TABLEPAGESIZE, int(self.lineedit_page.text()))
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_LOWSPECMODE, str(self.checkbox_lowspec.isChecked()))
        self.accept()


class LoadOptionDialog(QDialog):
    def __init__(self, is_already_loaded):
        super().__init__()
        self.is_already_loaded = is_already_loaded

        # 기본
        self.setWindowTitle("불러오기")
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(create_empty(minimum_height=1))

        # 라디오그룹 - 불러오기 모드
        groupBox_loadmode = QGroupBox("불러오기 모드 선택")
        layout.addWidget(groupBox_loadmode)

        groupBoxLayout_loadmode = QVBoxLayout()
        groupBox_loadmode.setLayout(groupBoxLayout_loadmode)

        self.radio1_loadmode = QRadioButton("새로 불러오기")
        self.radio1_loadmode.setChecked(True)
        self.radio2_loadmode = QRadioButton("추가로 불러오기")
        self.radio3_loadmode = QRadioButton("PNU로 열 덧붙이기")
        groupBoxLayout_loadmode.addWidget(self.radio1_loadmode)
        groupBoxLayout_loadmode.addWidget(self.radio2_loadmode)
        groupBoxLayout_loadmode.addWidget(self.radio3_loadmode)
        if not is_already_loaded:
            self.radio2_loadmode.setEnabled(False)
            self.radio3_loadmode.setEnabled(False)

        # # 라디오그룹 - 열 분리자 선택
        # groupBox_seperator = QGroupBox("열 분리자 선택")
        # layout.addWidget(groupBox_seperator)

        # groupBoxLayout_seperator = QVBoxLayout()
        # groupBox_seperator.setLayout(groupBoxLayout_seperator)

        # self.radio1_seperator = QRadioButton("| (버티컬바)")
        # self.radio1_seperator.setChecked(True)
        # self.radio2_seperator = QRadioButton(", (쉼표)")
        # groupBoxLayout_seperator.addWidget(self.radio1_seperator)
        # groupBoxLayout_seperator.addWidget(self.radio2_seperator)

        layout.addWidget(create_empty(minimum_height=1))

        # 예 아니오 박스
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.addWidget(buttonBox)

    def accept(self):
        if self.radio1_loadmode.isChecked():
            self.selected_radiovalue = ENUM_LOAD_MODE.NEW
        elif self.radio2_loadmode.isChecked():
            self.selected_radiovalue = ENUM_LOAD_MODE.APPEND
        elif self.radio3_loadmode.isChecked():
            self.selected_radiovalue = ENUM_LOAD_MODE.ADDROW

        # if self.radio1_seperator.isChecked():
        #     self.selected_seperator = ENUM_SEPERATOR.VERTICAL_BAR
        # elif self.radio2_seperator.isChecked():
        #     self.selected_seperator = ENUM_SEPERATOR.COMMA

        super().accept()


class CoordDialog(QDialog):
    def __init__(self, gui):
        self.gui = gui

        super(CoordDialog, self).__init__(parent=gui)

        self.setWindowTitle("좌표로 찾기")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("X, Y를 입력하십시오"), stretch=1)

        edit_hbox = QHBoxLayout()
        layout.addLayout(edit_hbox)

        label_x = QLabel("X: ")
        edit_hbox.addWidget(label_x)
        lineedit_x = QLineEdit(self)
        edit_hbox.addWidget(lineedit_x)
        label_y = QLabel("Y: ")
        edit_hbox.addWidget(label_y)
        lineedit_y = QLineEdit(self)
        edit_hbox.addWidget(lineedit_y)

        self.comboBox = QComboBox()
        for key, value in CONST_COORDSYS_STRMAP.items():
            self.comboBox.addItem(f"{key}:{value}", key)
        layout.addWidget(self.comboBox)

        self.lineedit_x = lineedit_x
        self.lineedit_y = lineedit_y

        find_button = QPushButton("찾기")
        find_button.clicked.connect(self.on_click_find_button)
        layout.addWidget(find_button)

        self.setLayout(layout)

    def on_click_find_button(self):
        x = self.lineedit_x.text()
        y = self.lineedit_y.text()
        coordsys = self.comboBox.currentData()

        if not is_float(x) or not is_float(y):
            QMessageBox.information(self, '경고', "잘못된 좌표입니다.")
            return

        try:
            x, y = transform_to_epsg4326(x, y, int(coordsys))
        except Exception as e:
            QMessageBox.information(self, '경고', f"좌표 변환 중 에러가 발생했습니다.\n\n{e}")
            return

        apikey = self.gui.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        if not apikey:
            QMessageBox.information(self, '경고', "상단메뉴에서 VWorld API를 등록해주세요.")
            return

        epsg = [x, y]
        addr = get_addr_from_epsg(apikey, epsg)

        self.gui.open_img({
            "epsg": epsg,
            "addr": addr
        })


class SimpleInputDialog(QDialog):
    def __init__(self, parent, title, content, text=""):
        super().__init__(parent)
        self.initUI(title, content, text)

    def initUI(self, title, content, text):
        self.setWindowTitle(title)

        self.layout = QVBoxLayout(self)

        self.label = QLabel(content, self)
        self.layout.addWidget(self.label, stretch=1)

        self.layout.addSpacing(10)

        self.text_input = QLineEdit(self)
        self.text_input.setMinimumHeight(30)
        self.text_input.setText(text)
        self.layout.addWidget(self.text_input, stretch=1)

        self.layout.addSpacing(10)

        self.button_box = QPushButton('확인', self)
        self.button_box.clicked.connect(self.accept)
        self.layout.addWidget(self.button_box, stretch=1)

        self.setLayout(self.layout)

    def getText(self):
        return self.text_input.text()


class SaveOptionDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("저장하기")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("저장하기 옵션 선택"), stretch=1)

        layout.addWidget(create_empty(minimum_height=5))

        self.list_groupbox = []
        for text_list in LIST_GROUPBOX_TEXT:
            title = text_list[0]
            content_list = text_list[1]

            groupBox_seperator = QGroupBox(title)
            groupBoxLayout = QVBoxLayout()
            groupBox_seperator.setLayout(groupBoxLayout)
            layout.addWidget(groupBox_seperator, stretch=1)

            list_groupboxdata = []
            for content in content_list:
                radio = QRadioButton(content)
                groupBoxLayout.addWidget(radio)
                list_groupboxdata.append(radio)
            self.list_groupbox.append(list_groupboxdata)

            list_groupboxdata[0].setChecked(True)

        layout.addWidget(create_empty(minimum_height=1))

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def accept(self):
        self.list_selected_value = []
        for list_gbdata in self.list_groupbox:
            for index, radio in enumerate(list_gbdata):
                if radio.isChecked():
                    self.list_selected_value.append(index)
                    break

        super().accept()


class FuncLoadingWorker(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        result = False
        try:
            result = self.func()
        except Exception as e:
            print(e)
            result = False

        self.finished.emit(result)


class FuncLoadingDialog(QDialog):
    def __init__(self, text, func):
        super().__init__()
        self.text = text
        self.func = func
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("로딩 중")

        layout = QVBoxLayout()
        self.progress_label = QLabel(self.text)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

        self.resize(200, 100)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def showEvent(self, event):
        self.worker_thread = FuncLoadingWorker(self.func)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()
        super().showEvent(event)

    def on_finished(self, b):
        self.result = b
        self.accept()


class FileLoadingWorker(QThread):
    finished = pyqtSignal(pd.DataFrame)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        df = pd.DataFrame()
        try:
            df = self.func()
            if df is None:
                df = pd.DataFrame()
        except Exception as e:
            print(e)
            self.finished.emit(pd.DataFrame())

        self.finished.emit(df)


# Warning!
# finished always return dataframe
# if failed, dataframe.empty will be return.
# you should check "if df.empty:" instead "if df:"
class FileIODialog(QDialog):
    def __init__(self, text, func):
        super().__init__()
        self.text = text
        self.func = func
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("로딩 중")

        layout = QVBoxLayout()
        self.progress_label = QLabel(self.text)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

        self.resize(200, 100)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def showEvent(self, event):
        self.worker_thread = FileLoadingWorker(self.func)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()
        super().showEvent(event)

    def on_finished(self, df):
        self.result = df
        self.accept()


# addr, epsg를 주면 알아서 기존 세팅과 api_key를 때마다 받아와 요청한다.
class ImageViewerDialog(QDialog):
    def __init__(self, parent, addr, epsg):
        super(ImageViewerDialog, self).__init__(parent=parent)

        self.epsg = epsg

        self.setWindowTitle(
            f"{addr} (정확한 위치가 아닐 수 있습니다. 이 창은 독립적입니다.)")
        self.move(parent.settings.value("ivd_pos", QPoint(300, 300)))
        self.resize(parent.settings.value("ivd_size", QSize(480, 480)))

        # main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # image
        self.image_result = ImageViewerDialog.CustomImageView()
        self.installEventFilter(self.image_result)
        layout.addWidget(self.image_result)

        # options
        # Get Values
        ivd_zoom = self.parent().settings.value(SAVE_KEY_MAP.IVD_ZOOM, 18)
        ivd_width = self.parent().settings.value(SAVE_KEY_MAP.IVD_WIDTH, 1024)
        ivd_height = self.parent().settings.value(SAVE_KEY_MAP.IVD_HEIGHT, 1024)
        ivd_basemap = self.parent().settings.value(
            SAVE_KEY_MAP.IVD_BASEMAP, ENUM_STATICMAP_BASEMAP.PHOTO_HYBRID)

        # Option layout
        option_layout = QHBoxLayout()
        layout.addLayout(option_layout)

        # Zoom
        self.zoom_label = QLabel("줌: 18")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(6)
        self.zoom_slider.setMaximum(18)
        self.zoom_slider.setValue(ivd_zoom)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)
        option_layout.addWidget(self.zoom_label)
        option_layout.addWidget(self.zoom_slider)

        # Width
        self.width_label = QLabel("너비:")
        self.width_edit = QLineEdit(str(ivd_width))
        self.width_edit.setValidator(QIntValidator(0, 1024))
        self.width_edit.textChanged.connect(self.update_width_edit)
        option_layout.addWidget(self.width_label)
        option_layout.addWidget(self.width_edit)

        # Height
        self.height_label = QLabel("높이:")
        self.height_edit = QLineEdit(str(ivd_height))
        self.height_edit.setValidator(QIntValidator(0, 1024))
        self.height_edit.textChanged.connect(self.update_height_edit)
        option_layout.addWidget(self.height_label)
        option_layout.addWidget(self.height_edit)

        # Basemap
        self.basemap_label = QLabel("종류:")
        self.basemap_combo = QComboBox()
        self.basemap_combo.addItems(list(ENUM_STATICMAP_BASEMAP))
        self.basemap_combo.setCurrentText(ivd_basemap)
        option_layout.addWidget(self.basemap_label)
        option_layout.addWidget(self.basemap_combo)

        # Ok Button
        self.refresh_button = QPushButton("반영")
        self.refresh_button.clicked.connect(self.refresh_img)
        option_layout.addWidget(self.refresh_button)

        self.refresh_img()

    class CustomImageView(QLabel):
        def __init__(self):
            self.is_inited = False

            super(ImageViewerDialog.CustomImageView, self).__init__()
            self.setAlignment(Qt.AlignCenter)
            self.setStyleSheet("""
                background-position: center
            """)

        def set_custom_pixmap(self, img_obj):
            self.is_inited = True
            self.pixmap = img_obj
            self.refresh_size()

        def refresh_size(self):
            if self.is_inited:
                self.setPixmap(self.pixmap.scaled(
                    self.width(), self.height(),
                    aspectRatioMode=Qt.KeepAspectRatio,
                    transformMode=Qt.SmoothTransformation))
                self.setMinimumWidth(100)

        def eventFilter(self, obj, event):
            if event.type() == QEvent.Resize:
                self.refresh_size()
                return True
            return super(ImageViewerDialog.CustomImageView, self).eventFilter(obj, event)

    def refresh_img(self):
        # 0. 옵션 가져오기
        ivd_zoom = self.zoom_slider.value()
        ivd_width = self.width_edit.text()
        ivd_height = self.height_edit.text()
        ivd_basemap = self.basemap_combo.currentText()

        if not ivd_width:
            self.width_edit.setText("1024")
            ivd_width = 1024

        if not ivd_height:
            self.height_edit.setText("1024")
            ivd_height = 1024

        # 1. id / secret 체크
        api_key = self.parent().settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        if not api_key:
            QMessageBox.information(
                self, '경고', "옵션에서 브이월드 API Key를 설정해주세요.")

            self.reserve_close()
            return

        # 2. 접속
        is_success, content = get_map_img(
            api_key, self.epsg, ivd_zoom, ivd_width, ivd_height, ivd_basemap)
        if not is_success:
            QMessageBox.information(
                self, '경고', "브이월드에 접속하는데 실패했습니다.\n\n" + str(content))
            self.reserve_close()
            return

        # 3. image_data -> pixmap 전환
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(content)
            self.image_result.set_custom_pixmap(pixmap)
        except Exception as e:
            QMessageBox.information(
                self, '경고', "이미지를 변환하는데 실패했습니다.\n\n" + str(e))
            self.reserve_close()
            return

        # 4. 설정 저장
        self.parent().settings.setValue(SAVE_KEY_MAP.IVD_ZOOM, ivd_zoom)
        self.parent().settings.setValue(SAVE_KEY_MAP.IVD_WIDTH, ivd_width)
        self.parent().settings.setValue(SAVE_KEY_MAP.IVD_HEIGHT, ivd_height)
        self.parent().settings.setValue(SAVE_KEY_MAP.IVD_BASEMAP, ivd_basemap)

    def update_zoom_label(self, value):
        if int(value) > 18 or int(value) < 6:
            QMessageBox.information(
                self, '경고', "zoom은 6이상 18이하여야합니다.")
            return
        self.zoom_label.setText(f"줌: {value}")

    def update_width_edit(self, value):
        if value and not (0 <= int(value) <= 1024):
            QMessageBox.information(
                self, '경고', "너비는 0 이상 1024 이하여야합니다.")
            self.width_edit.setText("1024")

    def update_height_edit(self, value):
        if value and not (0 <= int(value) <= 1024):
            QMessageBox.information(
                self, '경고', "높이는 0 이상 1024 이하여야합니다.")
            self.height_edit.setText("1024")

    def reserve_close(self):
        QTimer.singleShot(100, self.close)

    def closeEvent(self, e):
        self.parent().settings.setValue("ivd_pos", self.pos())
        self.parent().settings.setValue("ivd_size", self.size())
        e.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # DEBUG_MODE = OptionDialog
    # DEBUG_MODE = LoadOptionDialog
    # DEBUG_MODE = SaveOptionDialog
    # DEBUG_MODE = FileIODialog
    DEBUG_MODE = CoordDialog

    if DEBUG_MODE == OptionDialog:
        from PyQt5.QtWidgets import QMainWindow
        from PyQt5.QtCore import QSettings
        TOP_NAME = "mgj"
        APP_NAME = "mgj_csv_label_adder"
        qw = QMainWindow()
        qw.settings = QSettings(TOP_NAME, APP_NAME)
        loading_dialog = OptionDialog(qw)
        if loading_dialog.exec_() == QDialog.Accepted:
            print(len(loading_dialog.result))

    if DEBUG_MODE == CoordDialog:
        from PyQt5.QtWidgets import QMainWindow
        from PyQt5.QtCore import QSettings
        TOP_NAME = "mgj"
        APP_NAME = "mgj_csv_label_adder"
        qw = QMainWindow()
        qw.settings = QSettings(TOP_NAME, APP_NAME)
        loading_dialog = CoordDialog(qw)
        if loading_dialog.exec_() == QDialog.Accepted:
            print(len(loading_dialog.result))

    if DEBUG_MODE == LoadOptionDialog:
        loading_dialog = LoadOptionDialog()
        if loading_dialog.exec_() == QDialog.Accepted:
            print(len(loading_dialog.result))

    if DEBUG_MODE == SaveOptionDialog:
        loading_dialog = SaveOptionDialog()
        if loading_dialog.exec_() == QDialog.Accepted:
            print(len(loading_dialog.result))

    if DEBUG_MODE == FileIODialog:
        loading_dialog = FileIODialog(
            "csv 파일을 읽고 있습니다.",
            lambda: pd.read_csv("original.csv", encoding="euc-kr", sep="|", dtype=object))
        if loading_dialog.exec_() == QDialog.Accepted:
            print(loading_dialog.result)
