import os

from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox, QFileSystemModel, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from consts import SAVE_KEY_MAP


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
        lineedit_key.setText(self.parent.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, ""))
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
