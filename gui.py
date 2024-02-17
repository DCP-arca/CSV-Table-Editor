import json
import sys
import time

from io import BytesIO
from PIL import Image
from urllib import request

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QWidget, QTextEdit
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QMessageBox, QDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QSettings, QPoint, QSize, QCoreApplication
from qt_material import apply_stylesheet

from csv_label_adder import CSVLabelAdder

TITLE_NAME = "CSV Label Adder"
TOP_NAME = "mgj"
APP_NAME = "mgj_csv_label_adder"


class MyWidget(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.init_window()
        self.init_content()
        self.show()

    def init_window(self):
        self.setWindowTitle(TITLE_NAME)
        self.settings = QSettings(TOP_NAME, APP_NAME)
        self.move(self.settings.value("pos", QPoint(300, 300)))
        self.resize(self.settings.value("size", QSize(512, 768)))
        self.setAcceptDrops(False)

    def init_content(self):
        widget = QWidget()
        self.setCentralWidget(widget)

        vbox = QVBoxLayout()

        b = QPushButton("asd")
        vbox.addWidget(b)
        widget.setLayout(vbox)

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
