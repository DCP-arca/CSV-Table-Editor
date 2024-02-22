import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QGroupBox, QRadioButton, QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
        super().exec_()

    def initUI(self):
        parent_pos = self.parent.pos()

        self.setWindowTitle('옵션')
        self.move(parent_pos.x() + 50, parent_pos.y() + 50)
        self.resize(400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        hbox_key = QHBoxLayout()
        layout.addLayout(hbox_key)

        label_key = QLabel('키 입력:')
        hbox_key.addWidget(label_key)

        lineedit_key = QLineEdit(self)
        lineedit_key.setPlaceholderText("API 키를 입력해주세요.")
        lineedit_key.setText(self.parent.settings.value(
            SAVE_KEY_MAP.OPTION_APIKEY, ""))
        self.lineedit_key = lineedit_key
        hbox_key.addWidget(lineedit_key)

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
            SAVE_KEY_MAP.OPTION_APIKEY, self.lineedit_key.text())
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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loading_dialog = FileIODialog(
        "csv 파일을 읽고 있습니다.",
        lambda: pd.read_csv("massive_original.csv", encoding="euc-kr", sep="|", dtype=object))
    if loading_dialog.exec_() == QDialog.Accepted:
        print(len(loading_dialog.result))

    sys.exit(app.exec_())
