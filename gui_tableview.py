import sys
from PyQt5.QtWidgets import QApplication, QTableView, QDialog, QMenu, QCheckBox, QDialogButtonBox, QGridLayout, QMessageBox, QAbstractItemView, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator, QPainter, QColor, QFont
import pandas as pd

from consts import ENUM_STR_MAP, ENUM_TABLEVIEW_SORTMODE, ENUM_TABLEVIEW_INITMODE

# 페이지만들고 넘기기 만들기
# 표클릭 정렬 만들기
# 선택만들기
# 표클릭후 우클릭 만들기

DIALOG_GRID_WIDTH = 8
DEFAULT_TABLEVIEW_PAGE_SIZE = 20


class CustomInputDialog(QDialog):
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


class ColumnSelectionDialog(QDialog):
    def __init__(self, parent, column_names, current_selected_columns):
        super().__init__(parent)
        self.parent = parent
        self.column_names = column_names
        self.column_checkboxes = []

        self.init_ui(current_selected_columns)

    def init_ui(self, current_selected_columns):
        self.setWindowTitle("Column Selection")

        layout = QGridLayout()

        for index, col in enumerate(self.column_names):
            checkbox = QCheckBox(col)
            if col in current_selected_columns:
                checkbox.setChecked(True)
            self.column_checkboxes.append(checkbox)
            layout.addWidget(checkbox, int(
                index / DIALOG_GRID_WIDTH), index % DIALOG_GRID_WIDTH)

        button_layout = QVBoxLayout()
        layout.addLayout(button_layout, int(
            len(self.column_names) / DIALOG_GRID_WIDTH) + 1, DIALOG_GRID_WIDTH - 1)

        checkbuttons_layout = QHBoxLayout()
        button_layout.addLayout(checkbuttons_layout)
        button_allcheck = QPushButton("모두 선택")
        button_allcheck.pressed.connect(self.check_all)
        checkbuttons_layout.addWidget(button_allcheck)
        button_alluncheck = QPushButton("모두 해제")
        button_alluncheck.pressed.connect(self.uncheck_all)
        checkbuttons_layout.addWidget(button_alluncheck)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_columns(self):
        selected_columns = []
        for checkbox in self.column_checkboxes:
            if checkbox.isChecked():
                selected_columns.append(checkbox.text())
        return selected_columns

    def check_all(self):
        for box in self.column_checkboxes:
            box.setChecked(True)

    def uncheck_all(self):
        for box in self.column_checkboxes:
            box.setChecked(False)


# 다른것은 바꿀 필요없는 템플릿. 단지 headerData에서 좌, 상의 아이템를 볼 수 있는 것과 page시스템을 위해 data가 변경되어있다는 것.
class PandasModel(QAbstractTableModel):
    def __init__(self, parent, data, page_size):
        super(QAbstractTableModel, self).__init__(parent=parent)
        self._parent = parent
        self._data = data
        self._page_size = page_size
        self._current_page = 0
        # 0 == code / 1 == name / 2 == code(name)
        self.column_name_mode = False

    def rowCount(self, parent=None):
        return min(self._page_size, len(self._data) - self._current_page * self._page_size)

    def columnCount(self, parent=None):
        return self._data.shape[1] if not self._data.empty else 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                column_code = self._data.columns[section]
                result = ""
                if self.column_name_mode == 0:
                    result = column_code
                elif self.column_name_mode == 1:
                    result = ENUM_STR_MAP[column_code]
                    # null check
                    result = result if result else column_code
                elif self.column_name_mode == 2:
                    name = ENUM_STR_MAP[column_code]
                    # null check
                    if name:
                        result = name + "(" + column_code + ")"
                    else:
                        result = column_code

                return result
            elif orientation == Qt.Vertical:
                check_str = "✔ " if section in self._parent._parent.list_check else "   "
                return check_str + str(section + 1 + self._page_size * self._current_page)
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row() + self._current_page * self._page_size, index.column()])


# 테이블뷰. 이 안에 PandasModel이 있음.
class CSVTableView(QTableView):
    def __init__(self, parent, select_callback, on_value_edit_callback, page_size, lowspec_mode):
        super(CSVTableView, self).__init__(parent)
        self.placeholder_text = ""

        self._parent = parent
        self.select_callback = select_callback
        self.on_value_edit_callback = on_value_edit_callback
        self.page_size = page_size
        self.lowspec_mode = lowspec_mode
        self.setAcceptDrops(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        if self.lowspec_mode:
            return

        self.verticalHeader().setSectionsClickable(False)
        self.verticalHeader().sectionDoubleClicked.connect(
            self.parent().on_verticalheader_doubleclicked)
        self.horizontalHeader().setSectionsClickable(False)
        self.horizontalHeader().sectionDoubleClicked.connect(
            self.parent().on_horizontalheader_doubleclicked)

        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(
            self.open_horizontal_context_menu)

        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.verticalHeader().customContextMenuRequested.connect(
            self.open_vertical_context_menu)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self.open_table_context_menu)

    def refresh_tableview_width(self):
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
        self.verticalHeader().resizeSections(QHeaderView.ResizeToContents)

    def set_data(self, data):
        self.setModel(PandasModel(self, data, self.page_size))
        self.selectionModel().currentChanged.connect(self.select_callback)

    def set_data_with_init_column(self, data):
        self.set_data(data)
        self.refresh_tableview_width()
        self.set_sort_indicator(0, ENUM_TABLEVIEW_SORTMODE.ORIGINAL)
        for i in range(self.model().columnCount()):
            self.setColumnHidden(i, False)

    def get_page(self):
        return self.model()._current_page

    def get_maxpage(self):
        model = self.model()
        return int(len(model._data) / model._page_size) + 1

    def next_page(self):
        model = self.model()

        if (model._current_page + 1) * model._page_size < len(model._data):
            model._current_page += 1
            self.on_page_change()

    def prev_page(self):
        model = self.model()

        if model._current_page > 0:
            model._current_page -= 1
            self.on_page_change()

    def goto_page(self, page):
        self.model()._current_page = page - 1
        self.on_page_change()

    def set_sort_indicator(self, index, sort_mode):
        if sort_mode == ENUM_TABLEVIEW_SORTMODE.ASCEND:
            self.horizontalHeader().setSortIndicator(index, Qt.SortOrder.AscendingOrder)
            self.horizontalHeader().setSortIndicatorShown(True)
        elif sort_mode == ENUM_TABLEVIEW_SORTMODE.DESCEND:
            self.horizontalHeader().setSortIndicator(index, Qt.SortOrder.DescendingOrder)
            self.horizontalHeader().setSortIndicatorShown(True)
        elif sort_mode == ENUM_TABLEVIEW_SORTMODE.ORIGINAL:
            self.horizontalHeader().setSortIndicatorShown(False)

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
        font.setPointSize(14)
        painter.setFont(font)
        fm = self.fontMetrics()
        elided_text = fm.elidedText(
            self.placeholder_text, Qt.ElideRight, self.viewport().width()
        )
        painter.drawText(self.viewport().rect(),
                         Qt.AlignCenter, elided_text)
        painter.restore()

    def set_placeholder_text(self, text):
        self.placeholder_text = text

    def open_horizontal_context_menu(self, position):
        self._handle_hv_context_menu(True, position)

    def open_vertical_context_menu(self, position):
        self._handle_hv_context_menu(False, position)

    def _handle_hv_context_menu(self, is_h, position):
        str_header = "행" if is_h else "열"

        header = self.horizontalHeader() if is_h else self.verticalHeader()
        pos = header.logicalIndexAt(position)
        context_menu = QMenu(self)

        str_menu_list = ["새로 만들기", "복제", "제거", "복사", "덮어쓰기"]

        for str_menu in str_menu_list:
            action = context_menu.addAction(str_header + " " + str_menu)
            action.triggered.connect(
                lambda checked, hv=is_h, p=pos, s=str_menu: self.on_hb_contextmenu_triggered(hv, p, s))

        context_menu.exec_(header.viewport().mapToGlobal(position))

    def open_table_context_menu(self, position):
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            col = indexes[0].column()
            context_menu = QMenu(self)

            action = context_menu.addAction("수정")

            action.triggered.connect(
                lambda: self.on_table_contextmenu_triggered(row, col))

            context_menu.exec_(
                self.viewport().mapToGlobal(position))

    def on_hb_contextmenu_triggered(self, is_h, pos, str_menu):
        print(is_h, pos, str_menu)

    def on_table_contextmenu_triggered(self, row, col):
        if True:  # 수정
            target_index = row + (self.get_page()) * self.page_size
            target_df = self.model()._data.iloc[target_index]

            dialog = CustomInputDialog(self, '내용 수정', '수정할 내용을 입력하세요.', target_df[col])
            if dialog.exec_() == QDialog.Accepted:
                self.on_value_edit_callback(row, col, dialog.getText())

    def on_page_change(self):
        self.model().layoutChanged.emit()
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)


# 제일 위에 있는 QVBoxLayout
# 자식으로는 버튼들과 table_view
class CSVTableWidget(QWidget):
    on_columnselect_changed = pyqtSignal(list)
    on_columnsort_asked = pyqtSignal(int, str, int)
    on_page_refreshed = pyqtSignal()

    # select_callback : def func(self, cur, prev) 를 받습니다. connect를 지원하지 않아서 직접 건내줘야함
    # on_value_edit_callback : def func(self, row, col, value) 를 받습니다.
    # page_size : 한 페이지에 보여주는 행 갯수
    def __init__(self, parent, select_callback, on_value_edit_callback, page_size, lowspec_mode):
        super().__init__()
        self.list_check = []

        self._parent = parent
        self.page_size = page_size
        self.lowspec_mode = lowspec_mode

        self.layout = QVBoxLayout()

        upper_button_layout = QHBoxLayout()
        self.layout.addLayout(upper_button_layout)

        self.uncheck_button = QPushButton("체크 모두 해제하기")
        upper_button_layout.addWidget(self.uncheck_button)
        self.uncheck_button.clicked.connect(self.reset_check)
        self.string_button = QPushButton("열(라벨) 코드 <-> 뜻 전환")
        upper_button_layout.addWidget(self.string_button)
        self.string_button.clicked.connect(self.toggle_code_to_string)
        self.column_button = QPushButton("열(라벨) 보이기 / 숨기기")
        upper_button_layout.addWidget(self.column_button)
        self.column_button.clicked.connect(self.open_column_selection_dialog)

        self.table_view = CSVTableView(
            parent=self,
            select_callback=select_callback,
            on_value_edit_callback=on_value_edit_callback,
            page_size=page_size,
            lowspec_mode=lowspec_mode)
        self.layout.addWidget(self.table_view)

        self.lower_button_layout = QHBoxLayout()
        self.layout.addLayout(self.lower_button_layout)

        self.prev_button = QPushButton("이전")
        self.prev_button.clicked.connect(self.prev_page)
        self.lower_button_layout.addWidget(self.prev_button, stretch=4)

        self.lower_button_layout.addStretch(1)

        page_layout = QHBoxLayout()
        self.lower_button_layout.addLayout(page_layout)

        self.page_label = QLineEdit("1")
        self.page_label.setAlignment(Qt.AlignLeft)
        self.page_label.setMaximumWidth(60)
        self.page_label.returnPressed.connect(self.goto_page)
        page_layout.addWidget(self.page_label)

        self.maxpage_label = QLabel("/ n")
        self.maxpage_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        page_layout.addWidget(self.maxpage_label, stretch=1)

        self.lower_button_layout.addStretch(1)

        self.next_button = QPushButton("다음")
        self.next_button.clicked.connect(self.next_page)
        self.lower_button_layout.addWidget(self.next_button, stretch=4)

        self.enable_ui(False)
        self.setLayout(self.layout)

    def set_data(self, data, mode):
        self.data = data
        if self.lowspec_mode:
            self.enable_ui(True, [self.column_button])
            self.set_placeholder_text(
                "총 " + str(len(self._parent.dm.data)) + "개의 행이 로드 되었으며,\n현재 선택된 행은 " + str(len(data)) + "개 입니다.")  # TODO hardcoded

        if not self.lowspec_mode:
            self.enable_ui(True)
            if mode == ENUM_TABLEVIEW_INITMODE.LOAD:
                self.table_view.set_data_with_init_column(data)
                self.now_sort = []
            elif mode == ENUM_TABLEVIEW_INITMODE.SORT:
                self.table_view.set_data(data)
            elif mode == ENUM_TABLEVIEW_INITMODE.CONDITION:
                self.table_view.set_data(data)
                self.table_view.set_sort_indicator(
                    0, ENUM_TABLEVIEW_SORTMODE.ORIGINAL)
                self.now_sort = []

            self.init_page()

    # this function must be called after table_view.set_data

    def init_page(self):
        maxpage = self.table_view.get_maxpage()
        self.maxpage_label.setText("/ " + str(maxpage))
        self.page_label.setValidator(QIntValidator(1, maxpage))
        self.page_label.setText("1")
        self.refresh_page()

    def toggle_code_to_string(self):
        self.table_view.model().column_name_mode = 0 if self.table_view.model().column_name_mode + 1 > 2 \
            else self.table_view.model().column_name_mode + 1
        self.table_view.on_page_change()

    def open_column_selection_dialog(self):
        current_selected_columns = self._parent.showing_columns
        dialog = ColumnSelectionDialog(
            self, self.data.columns, current_selected_columns)
        if dialog.exec_():
            selected_columns = dialog.get_selected_columns()

            if len(selected_columns) == 0:
                QMessageBox.information(self, '경고', "적어도 하나는 선택해주세요.")
                return
            if not self.lowspec_mode:
                for col in self.data.columns:
                    col_index = self.data.columns.get_loc(col)
                    self.table_view.setColumnHidden(
                        col_index, col not in selected_columns)
            self.on_columnselect_changed.emit(selected_columns)

    def goto_page(self):
        page = self.get_page()
        if 1 <= page <= self.table_view.get_maxpage():
            self.table_view.goto_page(page)
        self.refresh_page()

    def next_page(self):
        self.table_view.next_page()
        self.refresh_page()

    def prev_page(self):
        self.table_view.prev_page()
        self.refresh_page()

    # 페이지 초기화시, 페이지 이동시(찍어서 가기, 앞으로, 뒤로)에 호출됨.
    def refresh_page(self):
        self.page_label.setText(str(self.table_view.get_page() + 1))
        self.reset_check()
        self.on_page_refreshed.emit()

    def get_page(self):
        return int(self.page_label.text())

    def enable_ui(self, is_disabled, list_target=[]):
        list_target = list_target or [self.page_label, self.prev_button, self.next_button, self.column_button,
                                      self.uncheck_button, self.string_button]
        for t in list_target:
            t.setEnabled(is_disabled)

    def set_placeholder_text(self, text):
        self.table_view.set_placeholder_text(text)

    def reset_check(self):
        self.list_check = []

        if self.lowspec_mode:
            return
        self.table_view.on_page_change()

    def on_verticalheader_clicked(self, index):
        print(index)

    def on_verticalheader_doubleclicked(self, index):
        if index in self.list_check:
            self.list_check.remove(index)
        else:
            self.list_check.append(index)

        self.table_view.on_page_change()

    # sorting
    def on_horizontalheader_doubleclicked(self, index):
        column_name = self.table_view.model().headerData(index, Qt.Horizontal)

        sort_mode = -1

        # 처음 정렬
        if not self.now_sort:
            sort_mode = ENUM_TABLEVIEW_SORTMODE.ASCEND
        else:
            if self.now_sort[0] == index:   # 같은 걸 한번 더 누른경우
                sort_mode = self.now_sort[1] + 1
                if sort_mode > 2:
                    sort_mode = 0
            else:                           # 다른 걸 누른 경우
                sort_mode = ENUM_TABLEVIEW_SORTMODE.ASCEND

        if sort_mode != -1:
            self.on_columnsort_asked.emit(index, column_name, sort_mode)

    def on_columnsort_answered(self, index, column_name, sort_mode):
        self.now_sort = [index, sort_mode]
        self.table_view.set_sort_indicator(index, sort_mode)


if __name__ == '__main__':
    from theme import apply_theme
    app = QApplication(sys.argv)
    apply_theme(app, 13)  # 테마적용

    table_widget = CSVTableWidget(
        app, lambda: print("select_callback 콜"), lambda: print("on_value_edit_callback 콜"), 20, False)

    table_widget.set_placeholder_text("")

    table_widget.set_data(pd.read_csv(
        "test_datas/test.csv", encoding="euc-kr", sep="|", dtype=object), 0)

    table_widget.show()
    sys.exit(app.exec_())
