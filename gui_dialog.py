import os
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QGroupBox, QRadioButton, QDialogButtonBox
from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from consts import SAVE_KEY_MAP, CODE_LOADMODE


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

        self.setWindowTitle("불러오기")
        self.layout = QVBoxLayout()

        self.groupBox = QGroupBox("불러오기 모드 선택")
        self.radio1 = QRadioButton("새로 불러오기")
        self.radio1.setChecked(True)
        self.radio2 = QRadioButton("추가로 불러오기")
        self.radio3 = QRadioButton("PNU로 열 덧붙이기")

        self.groupBoxLayout = QVBoxLayout()
        self.groupBoxLayout.addWidget(self.radio1)
        self.groupBoxLayout.addWidget(self.radio2)
        self.groupBoxLayout.addWidget(self.radio3)
        self.groupBox.setLayout(self.groupBoxLayout)

        self.layout.addWidget(self.groupBox)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def accept(self):
        if self.radio1.isChecked():
            self.selected_radiovalue = CODE_LOADMODE.NEW
        elif self.radio2.isChecked():
            self.selected_radiovalue = CODE_LOADMODE.APPEND
        elif self.radio3.isChecked():
            self.selected_radiovalue = CODE_LOADMODE.ADDROW

        super().accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoadOptionDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("선택된 라디오 버튼:", dialog.selected_radiovalue)
    sys.exit(app.exec_())
