from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QLabel, QComboBox, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt

from network import get_api_data
from consts import SAVE_KEY_MAP, CONST_NETWORK_APISTRMAP

class APITable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.clear()

    def clear_table(self):
        self.setRowCount(0)
        self.setColumnCount(0)

    def set_data(self, data):
        self.clear_table()
        self.setRowCount(len(data))
        self.setColumnCount(2)
        for row, (key, value) in enumerate(data.items()):
            self.setItem(row, 0, QTableWidgetItem(str(key)))
            self.setItem(row, 1, QTableWidgetItem(str(value)))


class APIInfoLayout(QVBoxLayout):
    def __init__(self, parent):
        self.pnu = ""
        self.message_label = QLabel("", alignment=Qt.AlignCenter)
        self.message_label.setMinimumHeight(70)

        super().__init__()
        self.parent = parent
        api_type_label = QLabel("API 요청 설정:")
        self.addWidget(api_type_label)

        self.api_type_combo = QComboBox()
        self.api_type_combo.addItems(CONST_NETWORK_APISTRMAP.keys())
        self.api_type_combo.currentTextChanged.connect(
            self.on_combobox_changed)
        self.addWidget(self.api_type_combo)

        self.api_table = APITable()
        self.addWidget(self.api_table, stretch=1)

        self.addWidget(self.message_label)

        self.refresh()

    def set_pnu(self, pnu):
        self.pnu = pnu

        self.refresh()

    def clear(self):
        self.pnu = ""
        
        self.refresh()

    def refresh(self):
        self.message_label.hide()
        self.api_table.hide()

        # 1. check api
        apikey = self.parent.settings.value(SAVE_KEY_MAP.OPTION_APIKEY, "")
        if not apikey:
            self.show_message("API 키가 설정되지 않았습니다.")
            return

        # 2. check selected
        if not self.pnu:
            self.show_message("PNU가 포함된 행을 눌러주세요.")
            return

        # 3. connect, and check success
        api_type = CONST_NETWORK_APISTRMAP.get(self.api_type_combo.currentText(), "")
        if not api_type:
            return

        data = get_api_data(apikey, self.pnu, api_type)
        if not data:
            self.show_message("데이터를 가져오는데 실패했습니다.\n해당하는 데이터가 없거나 apikey가 잘못되었을 수 있습니다.")
            return

        self.api_table.set_data(data)
        self.api_table.show()

    def show_message(self, message):
        self.message_label.setText(message)
        self.message_label.show()

    def on_combobox_changed(self, __text):
        self.refresh()