import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QGroupBox, QRadioButton, QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt5.QtGui import QIntValidator
import pandas as pd

from consts import SAVE_KEY_MAP, ENUM_LOAD_MODE, ENUM_SEPERATOR, ENUM_FILEIO_DIALOG_MODE


LIST_GROUPBOX_TEXT = [
    ["열 분리자 선택", ["| (버티컬바)", ". (마침표)"]],
    ["열 내보내기", ["모두", "현재 보이는 열(라벨)만 내보내기"]],
    ["행 내보내기", ["모두", "체크된 행만 내보내기", "체크된 행을 select열로 추가해서 내보내기"]]
]


def create_empty(minimum_width=0, minimum_height=0):
    w = QWidget()
    w.setMinimumWidth(minimum_width)
    w.setMinimumHeight(minimum_height)
    return w


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
        self.le_naver_id = create_lineedit_key(
            'Naver Cloud Client ID 입력:', "API 키를 입력해주세요.", SAVE_KEY_MAP.OPTION_CLIENTID)
        self.le_naver_secret = create_lineedit_key(
            'Naver Cloud Client Secret 입력:', "API 키를 입력해주세요.", SAVE_KEY_MAP.OPTION_CLIENTSECRET)

        layout.addStretch(1)

        layout.addWidget(create_empty(minimum_height=10))

        hbox_font = QHBoxLayout()
        layout.addLayout(hbox_font)
        hbox_font.addWidget(QLabel("글자 크기 : "))
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
        layout.addWidget(QLabel("*행 갯수는 다음 실행부터 적용됩니다."))

        layout.addStretch(1)

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
            SAVE_KEY_MAP.OPTION_CLIENTID, self.le_naver_id.text())
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_CLIENTSECRET, self.le_naver_secret.text())
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_FONTSIZE, int(self.lineedit_font.text()))
        self.parent.settings.setValue(
            SAVE_KEY_MAP.OPTION_TABLEPAGESIZE, int(self.lineedit_page.text()))
        self.accept()


class LoadOptionDialog(QDialog):
    def __init__(self):
        super().__init__()

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

        # 라디오그룹 - 열 분리자 선택
        groupBox_seperator = QGroupBox("열 분리자 선택")
        layout.addWidget(groupBox_seperator)

        groupBoxLayout_seperator = QVBoxLayout()
        groupBox_seperator.setLayout(groupBoxLayout_seperator)

        self.radio1_seperator = QRadioButton("| (버티컬바)")
        self.radio1_seperator.setChecked(True)
        self.radio2_seperator = QRadioButton(". (마침표)")
        groupBoxLayout_seperator.addWidget(self.radio1_seperator)
        groupBoxLayout_seperator.addWidget(self.radio2_seperator)

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

        if self.radio1_seperator.isChecked():
            self.selected_seperator = ENUM_SEPERATOR.VERTICAL_BAR
        elif self.radio2_seperator.isChecked():
            self.selected_seperator = ENUM_SEPERATOR.DOT

        super().accept()


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


class LoadingWorker(QThread):
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
        self.worker_thread = LoadingWorker(self.func)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()
        super().showEvent(event)

    def on_finished(self, df):
        self.result = df
        self.accept()


class ImageViewerDialog(QDialog):
    def __init__(self, parent, title, pixmap):
        super(ImageViewerDialog, self).__init__(parent=parent)
        self.setWindowTitle(
            "{title} (정확한 위치가 아닐 수 있습니다. 이 창은 독립적입니다.)".format(title=title))

        class CustomImageView(QLabel):
            def __init__(self, first_src):
                super(CustomImageView, self).__init__()
                self.set_custom_pixmap(first_src)

            def set_custom_pixmap(self, img_obj):
                self.pixmap = img_obj
                self.refresh_size()

            def refresh_size(self):
                self.setPixmap(self.pixmap.scaled(
                    self.width(), self.height(),
                    aspectRatioMode=Qt.KeepAspectRatio,
                    transformMode=Qt.SmoothTransformation))

            def eventFilter(self, obj, event):
                if event.type() == QEvent.Resize:
                    self.refresh_size()
                    return True
                return super(CustomImageView, self).eventFilter(obj, event)

        image_result = CustomImageView(pixmap)
        image_result.setAlignment(Qt.AlignCenter)
        image_result.setStyleSheet("""
            background-position: center
        """)
        self.installEventFilter(image_result)
        self.image_result = image_result

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.image_result)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loading_dialog = OptionDialog(app)
    if loading_dialog.exec_() == QDialog.Accepted:
        print(len(loading_dialog.result))

    sys.exit(app.exec_())
