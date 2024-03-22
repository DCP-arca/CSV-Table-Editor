import sys
from PyQt5.QtWidgets import QApplication, QFrame, QComboBox, QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QLineEdit, QAbstractItemView, QHBoxLayout, QListView, QMessageBox, QStyledItemDelegate
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont


class FilterStruct():
    def __init__(self,
                 column="",
                 min_val="",
                 max_val="",
                 str_val="",
                 qmodelindex=None):

        self.column = column
        self.min_val = min_val
        self.max_val = max_val
        self.str_val = str_val

        if qmodelindex:
            condition = qmodelindex.data()
            if '∈' in condition:
                self.column = condition.split()[2]
                self.str_val = condition.split()[0]
            else:
                self.column = condition.split()[2]
                self.min_val = condition.split()[0]
                self.max_val = condition.split()[4]

        if self.min_val:
            self.is_minmax_mode = True
        elif self.str_val:
            self.is_minmax_mode = False
        else:
            assert False, "Erorr"

    def to_string(self):
        if self.min_val:
            return f"{self.min_val} < {self.column} < {self.max_val}"
        else:
            return f"{self.str_val} ∈ {self.column}"


class ConditionDialog(QDialog):
    def __init__(self, parent, column_list, original_qmodelindex=None):
        super().__init__()
        self.is_minmax_mode = True

        self._parent = parent
        self.original_qmodelindex = original_qmodelindex
        self.setWindowTitle("조건 추가")
        layout = QVBoxLayout()

        self.column_label = QLabel("열(라벨):")
        self.column_combobox = QComboBox()
        self.column_combobox.addItems(column_list)

        self.mode_label = QLabel("비교 모드:")
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(['크기 비교', '문자 포함'])
        self.mode_combobox.currentIndexChanged.connect(
            self.on_moderadio_changed)

        self.frame_minmax = QFrame()
        layout_minmax = QVBoxLayout()
        self.frame_minmax.setLayout(layout_minmax)
        self.min_label = QLabel("이상:")
        self.min_input = QLineEdit()
        self.max_label = QLabel("이하:")
        self.max_input = QLineEdit()
        layout_minmax.addWidget(self.min_label)
        layout_minmax.addWidget(self.min_input)
        layout_minmax.addWidget(self.max_label)
        layout_minmax.addWidget(self.max_input)

        self.frame_str = QFrame()
        layout_str = QVBoxLayout()
        self.frame_str.setLayout(layout_str)
        self.str_label = QLabel("다음 텍스트를 포함:")
        self.str_input = QLineEdit()
        layout_str.addWidget(self.str_label)
        layout_str.addWidget(self.str_input)
        self.frame_str.setVisible(False)

        self.confirm_button = QPushButton("확인")
        self.confirm_button.clicked.connect(self.confirm_condition)

        layout.addWidget(self.column_label)
        layout.addWidget(self.column_combobox)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combobox)
        layout.addWidget(self.frame_minmax)
        layout.addWidget(self.frame_str)
        layout.addWidget(QFrame(), stretch=999)
        layout.addWidget(self.confirm_button)

        if original_qmodelindex:
            self.remove_button = QPushButton("제거")
            self.remove_button.clicked.connect(self.remove_condition)
            layout.addWidget(self.remove_button)

            fs = FilterStruct(qmodelindex=original_qmodelindex)
            column = fs.column

            if not (column in column_list):
                column_list.append(column)
            self.column_combobox.setCurrentText(column)

            self.change_searchmode(fs.is_minmax_mode)
            self.mode_combobox.setCurrentIndex(0 if fs.is_minmax_mode else 1)
            if fs.is_minmax_mode:
                self.min_input.setText(fs.min_val or "")
                self.max_input.setText(fs.max_val or "")
            else:
                self.str_input.setText(fs.str_val or "")

        self.setLayout(layout)

    def on_moderadio_changed(self, v):
        self.change_searchmode((v == 0))

    def change_searchmode(self, is_minmax_mode):
        self.is_minmax_mode = is_minmax_mode

        self.frame_minmax.setVisible(is_minmax_mode)
        self.frame_str.setVisible(not is_minmax_mode)

    def confirm_condition(self):
        column = self.column_combobox.currentText()

        if self.is_minmax_mode:
            min_val = self.min_input.text().strip()
            max_val = self.max_input.text().strip()

            if self._check_condition_value_minmax(column, min_val, max_val):
                item_text = FilterStruct(
                    column=column, min_val=min_val, max_val=max_val).to_string()
                self._parent.add_condition(
                    item_text, self.original_qmodelindex)
                self.close()
        else:
            str_val = self.str_input.text().strip()

            if self._check_condition_value_str(column, str_val):
                item_text = FilterStruct(
                    column=column, str_val=str_val).to_string()
                self._parent.add_condition(
                    item_text, self.original_qmodelindex)
                self.close()

    def remove_condition(self):
        self._parent.remove_condition(self.original_qmodelindex)
        self.close()

    def _check_condition_value_str(self, column, str_val):
        if not column:
            QMessageBox.warning(self, "경고", "열(라벨)의 이름을 입력해주세요.")
            return False
        if not str_val:
            QMessageBox.warning(self, "경고", "검색할 값을 넣어주세요.")
            return False
        if len(str_val) < 1 or len(str_val) > 120:
            QMessageBox.warning(
                self, "경고", "검색할 문자는 1자 이상, 120자 이하여야합니다.")
            return False

        return True

    def _check_condition_value_minmax(self, column, min_val, max_val):
        if not column:
            QMessageBox.warning(self, "경고", "열(라벨)의 이름을 입력해주세요.")
            return False
        if not min_val or not max_val:
            QMessageBox.warning(
                self, "경고", "이상/이하의 숫자를 입력해 주세요.")
            return False
        try:
            min_val = float(min_val)
            max_val = float(max_val)
        except ValueError:
            QMessageBox.warning(
                self, "경고", "이상/이하 칸에 올바른 숫자를 입력해주세요.")
            return False
        if len(column) < 1 or len(column) > 120:
            QMessageBox.warning(
                self, "경고", "열(라벨)의 이름은 1자 이상, 120자 이하여야합니다.")
            return False
        if min_val > max_val:
            QMessageBox.warning(
                self, "경고", "이상 칸의 숫자가 이하 칸의 숫자보다 큽니다.")
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

    def removeLastItem(self):
        if self.rowCount() > 0:
            self.beginRemoveRows(self.createIndex(
                0, 0), self.rowCount() - 1, self.rowCount() - 1)
            del self._data[-1]
            self.endRemoveRows()

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
    def __init__(self):
        super().__init__()
        self.placeholder_text = ""

    def set_info_text(self, text):
        self.placeholder_text = text

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.model() is not None and self.model().rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.save()
        col = QColor("#009688")  # self.palette().placeholderText().color()
        painter.setPen(col)
        font = QFont()
        font.setBold(True)
        # font.setPointSize(14)
        painter.setFont(font)
        fm = self.fontMetrics()
        elided_text = fm.elidedText(
            self.placeholder_text, Qt.ElideRight, self.viewport().width()
        )
        painter.drawText(self.viewport().rect(),
                         Qt.AlignCenter, elided_text)
        painter.restore()


class SearchWidget(QWidget):
    on_condition_changed = pyqtSignal(list, list)  # TODO hardcoded

    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()

        self.add_condition_button = QPushButton("추가")
        self.add_condition_button.setEnabled(False)
        self.add_condition_button.clicked.connect(self.show_condition_dialog)
        self.layout.addWidget(self.add_condition_button)

        self.internal_model = CircularListModel()  # 초기 아이템 설정
        list_view = PlaceholderTableView()
        list_view.setModel(self.internal_model)
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
        self.list_view = list_view
        self.layout.addWidget(list_view)

        self.enter_condition_button = QPushButton("반영")
        self.enter_condition_button.setEnabled(False)
        self.enter_condition_button.clicked.connect(
            self.on_click_entercondition)
        self.layout.addWidget(self.enter_condition_button)

        self.setLayout(self.layout)

    def show_condition_dialog(self):
        dialog = ConditionDialog(self, self.columns)
        dialog.exec_()

    def show_edit_dialog(self, item):
        dialog = ConditionDialog(self, self.columns, item)
        dialog.exec_()

    def initialize(self, columns):
        self.internal_model.clearAll()

        self.set_columns(columns)

        self.add_condition_button.setEnabled(True)
        self.enter_condition_button.setEnabled(True)
        self.enter_condition_button.setStyleSheet(
            "QPushButton{color: #009688;}")

    def set_columns(self, columns):
        self.columns = columns

    # original_qmodelindex가 존재하면 edit함.
    def add_condition(self, condition, original_qmodelindex=None):
        # original_data = []
        if not original_qmodelindex:
            self.internal_model.addItem(condition)
        else:
            # original_data = [original_qmodelindex, get_condition_from_qmodelindex(
            #     original_qmodelindex)]
            self.internal_model.editItem(original_qmodelindex, condition)
        self.enter_condition_button.setStyleSheet("QPushButton{color: red;}")

        # self._func_on_condition_changed(original_data)

    def remove_condition(self, target_index):
        self.internal_model.removeRow(target_index)

        # self._func_on_condition_changed()

    def set_info_text(self, text):
        self.list_view.set_info_text(text)

    # 단순히 아이템을 수정한다. datamanager가 수정 실패시 gui로부터 호출됨
    def on_edit_failed(self, original_cond):
        self.internal_model.clearAll()
        for cond in original_cond:
            self.add_condition(cond)

    def on_click_entercondition(self):
        self.on_condition_changed.emit(
            self.internal_model._data.copy(), [])
        self.enter_condition_button.setStyleSheet(
            "QPushButton{color: #009688;}")

    # add일때는 인자가 없다. edit일때만 original_data가 넘어온다.
    # original_data안에는 0:original_qmodelindex(QModelIndex), 1:original_condition(str)가 있다.
    # QModelIndex.isValid함수로 null인지 아닌지 체크가능.
    def _func_on_condition_changed(self, original_data=[]):
        self.on_condition_changed.emit(
            self.internal_model._data.copy(), original_data)


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
    search_widget.show_condition_dialog()
    sys.exit(app.exec_())
