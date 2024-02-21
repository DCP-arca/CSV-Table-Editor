import sys
from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QLabel, QVBoxLayout, QWidget, QFrame
from PyQt5.QtCore import Qt

class RoundedWidget(QWidget):
    def __init__(self, parent=None):
        super(RoundedWidget, self).__init__(parent)
        self.setContentsMargins(10, 10, 10, 10)
        self.setObjectName("roundedWidget")
        self.setStyleSheet("#roundedWidget { background-color: lightblue; border-radius: 20px; }")


class CustomItem(QListWidgetItem):
    def __init__(self, text):
        super(CustomItem, self).__init__()

        widget = RoundedWidget()
        layout = QVBoxLayout()
        label = QLabel(text)
        layout.addWidget(label)
        widget.setLayout(layout)

        self.setSizeHint(widget.sizeHint())
        self.setText(text)
        self.setFlags(self.flags() |  Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.widget = widget


class MainWindow(QListWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Add custom items
        items = ["Item 1", "Item 2", "Item 3"]
        for item_text in items:
            custom_item = CustomItem(item_text)
            self.addItem(custom_item)
            self.setItemWidget(custom_item, custom_item.widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
