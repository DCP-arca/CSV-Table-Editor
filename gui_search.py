import sys
from PyQt5.QtWidgets import QApplication, QComboBox, QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QLineEdit, QAbstractItemView, QHBoxLayout, QListView, QListWidget, QListWidgetItem, QMessageBox, QStyledItemDelegate
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont
import pandas as pd


class ConditionDialog(QDialog):
    def __init__(self, parent, column_list, data=None):
        super().__init__()
        self._parent = parent
        self.setWindowTitle("Add/Edit Condition")
        layout = QVBoxLayout()

        column = ""
        min_val = ""
        max_val = ""
        self.data = data
        if data:
            condition = data.data()
            column = condition.split()[2]
            min_val = condition.split()[0]
            max_val = condition.split()[4]

            if not (column in column_list):
                column_list.append(column)

        self.column_label = QLabel("Column:")
        self.column_combobox = QComboBox()
        self.column_combobox.addItems(column_list)
        self.column_combobox.setCurrentText(column)
        self.min_label = QLabel("Min:")
        self.min_input = QLineEdit(min_val or "")
        self.max_label = QLabel("Max:")
        self.max_input = QLineEdit(max_val or "")

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.confirm_condition)

        layout.addWidget(self.column_label)
        layout.addWidget(self.column_combobox)
        layout.addWidget(self.min_label)
        layout.addWidget(self.min_input)
        layout.addWidget(self.max_label)
        layout.addWidget(self.max_input)
        layout.addWidget(self.confirm_button)

        if data:
            self.remove_button = QPushButton("Remove")
            self.remove_button.clicked.connect(self.remove_condition)
            layout.addWidget(self.remove_button)

        self.setLayout(layout)

    def confirm_condition(self):
        column = self.column_combobox.currentText()
        min_val = self.min_input.text().strip()
        max_val = self.max_input.text().strip()

        if self._check_condition_value(column, min_val, max_val):
            item_text = f"{min_val} < {column} < {max_val}"
            self._parent.add_condition(item_text, self.data)
            self.close()

    def remove_condition(self):
        self._parent.remove_condition(self.data)
        self.close()

    def _check_condition_value(self, column, min_val, max_val):
        if not column:
            QMessageBox.warning(self, "Warning", "Please enter a column name.")
            return False
        if not min_val or not max_val:
            QMessageBox.warning(
                self, "Warning", "Please enter both minimum and maximum values.")
            return False
        try:
            min_val = float(min_val)
            max_val = float(max_val)
        except ValueError:
            QMessageBox.warning(
                self, "Warning", "Please enter valid numeric values for min and max.")
            return False
        if len(column) < 1 or len(column) > 120:
            QMessageBox.warning(
                self, "Warning", "Column name must be between 1 and 120 characters long.")
            return False
        if min_val > max_val:
            QMessageBox.warning(
                self, "Warning", "Minimum value must be less than maximum value.")
            return False

        return True


class CircularListModel(QAbstractListModel):
    def __init__(self, data=[], parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()]

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self.beginRemoveRows(QModelIndex(), index.row(), index.row())
            self._data[index.row()] = value
            self.dataChanged.emit(index, index)
            self.endRemoveRows()
            return True
        return False

    def editItem(self, index, newValue):
        if index.isValid() and 0 <= index.row() < len(self._data):
            self.setData(index, newValue)

    def addItem(self, item):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def removeRow(self, index):
        if not index.isValid() or index.row() >= len(self._data):
            return False

        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        del self._data[index.row()]
        self.endRemoveRows()
        return True

    def clearAll(self):
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()


class CustomDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        # Draw outline for each item
        pen = painter.pen()
        pen.setColor(QColor(0, 150, 136))  # Outline color
        pen.setWidth(2)  # Outline width
        painter.setPen(pen)
        painter.drawRoundedRect(option.rect, 5, 5)

        # Call the default paint implementation
        super().paint(painter, option, index)

        painter.restore()


class PlaceholderTableView(QListView):
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.model() is not None and self.model().rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.save()
        col = self.palette().placeholderText().color()
        painter.setPen(col)
        font = QFont()
        font.setBold(True)
        # font.setPointSize(14)
        painter.setFont(font)
        fm = self.fontMetrics()
        elided_text = fm.elidedText(
            "왼쪽의 버튼을 눌러 필터를 추가!", Qt.ElideRight, self.viewport().width()
        )
        painter.drawText(self.viewport().rect(),
                         Qt.AlignCenter, elided_text)
        painter.restore()


class SearchWidget(QWidget):
    on_condition_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()

        self.add_condition_button = QPushButton("추가")
        self.add_condition_button.setEnabled(False)
        self.add_condition_button.clicked.connect(self.show_condition_dialog)
        self.layout.addWidget(self.add_condition_button)

        self.model = CircularListModel()  # 초기 아이템 설정
        list_view = PlaceholderTableView()
        list_view.setModel(self.model)
        list_view.setItemDelegate(CustomDelegate())
        list_view.setIconSize(QSize(100, 100))  # 아이콘 크기 조절
        # list_view.setViewMode(QListView.IconMode)
        list_view.setMovement(QListView.Static)  # 아이템 이동 금지
        list_view.setResizeMode(QListView.Adjust)  # 크기 자동 조절
        list_view.setFixedHeight(30)
        list_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        list_view.horizontalScrollBar().setSingleStep(10)
        list_view.setSizeAdjustPolicy(QListView.AdjustToContents)
        list_view.setSpacing(4)
        list_view.setFlow(QListView.Flow.LeftToRight)
        list_view.doubleClicked.connect(self.show_edit_dialog)
        self.layout.addWidget(list_view)

        self.setLayout(self.layout)

    def show_condition_dialog(self):
        dialog = ConditionDialog(self, self.columns)
        dialog.exec_()

    def show_edit_dialog(self, item):
        dialog = ConditionDialog(self, self.columns, item)
        dialog.exec_()

    def initialize(self, columns):
        self.model.clearAll()

        self.set_columns(columns)

        self.add_condition_button.setEnabled(True)

    def set_columns(self, columns):
        self.columns = columns

    def add_condition(self, condition, editing_index=None):
        if not editing_index:
            self.model.addItem(condition)
        else:
            self.model.editItem(editing_index, condition)

        self._func_on_condition_changed()

    def remove_condition(self, target_index):
        self.model.removeRow(target_index)

        self._func_on_condition_changed()

    def _func_on_condition_changed(self):
        self.on_condition_changed.emit(self.model._data.copy())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    search_widget = SearchWidget()
    search_widget.initialize(
        ['Columcsacsaasdasdasdsadscn3', 'Cn2', 'Columcsacsacn3'])
    # search_widget.add_condition("1 < col < 2")
    # search_widget.add_condition("1 < col < 2")
    # search_widget.add_condition("1 < col < 2")
    # search_widget.add_condition("1 < col < 2")
    search_widget.resize(800, 50)
    search_widget.show()
    sys.exit(app.exec_())
