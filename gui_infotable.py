import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
dataframes = {"STDMT": 1, "PNU": 43114107010368012, "LAND_SEQNO": 22035, "SGG_CD": 43114, "LAND_LOC_CD": 1070, "LAND_GBN": 1, "BOBN": 368, "BUBN": 12, "ADM_UMD_CD": 0, "PNILP": 4200, "CMPR_PJJI_NO1": 488, "CMPR_PJJI_NO2": 0, "LAND_GRP": -1, "BSIN_AREA": 0, "JIMOK": 0, "ACTL_JIMOK": 0, "PAREA": 785.000, "SPFC1_AREA": 785.0, "SPFC2_AREA": 0.0, "SPFC1": 42, "SPFC2": 0, "SPCFC": 130, "RSTA_ETC": 90, "RSTA_AREA_RATE": 10, "RSTA_ETC21": 0, "RSTA_ETC22": 0, "RSTA2_USE_YN": 0, "RSTA2_AREA_RATE": 10, "RSTA_UBPLFC1": 0, "CFLT_RT1": 0, "RSTA_UBPLFC2": 0, "CFLT_RT2": 0, "FARM_GBN": 0, "FRTL": 0, "LAND_ADJ": 0, "FRST1": 0, "FRST2": 0, "LAND_USE": 610, "LAND_USE_ETC": -1, "GEO_HL": 2, "GEO_FORM": 5, "GEO_AZI": 0, "ROAD_SIDE": 8,
              "ROAD_DIST": 0, "HARM_RAIL": 0, "HARM_WAST": 0, "LCLW_MTHD_CD": 0, "LCLW_STEP_CD": 0, "HANDWK_YN": 0, "PY_JIGA": 4450, "PREV_JIGA": 0, "CALC_JIGA": 4200, "VRFY_JIGA": 4200, "READ_JIGA": 4200, "OPN_SMT_JIGA": 0, "FOBJCT_JIGA": 0, "PY2_JIGA": 4150, "PY3_JIGA": 3990, "PY4_JIGA": 3900, "OWN_GBN": 4, "OWN_TYPE": 1, "EXAMER_OPN_CD": 0, "REV_CD": 0, "EXAMER_CD": 102, "CNFER_CD": 102, "VRFY_GBN": 2, "PY_VRFY_GBN": 2, "LAND_MOV_YMD": 2020101, "LAND_MOV_RSN_CD": 0, "HOUSE_PANN_YN": 0, "SPCFC2": 0, "RSTA_ETC2": 0, "LAND_USE_SOLAR": 0, "LAND_CON": 1, "DUP_AREA_RATE": 0, "GRAVE_GBN": 0, "GRAVE_AREA_RATE": 0, "HARM_SUBSTATION": 0, "GTX_GBN": 0, "PJJI_DIST1": 226.33, "PJJI_DIST2": -99.0, "DIFF_CD": 0, "COL_ADM_SECT_CD": 43110}


class InfoTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        self.placeholder_text = ""

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.model() is not None and self.model().rowCount() > 0:
            return
        painter = QPainter(self.viewport())
        painter.save()
        col = self.palette().placeholderText().color()
        painter.setPen(col)
        fm = self.fontMetrics()
        elided_text = fm.elidedText(
            self.placeholder_text, Qt.ElideRight, self.viewport().width()
        )
        painter.drawText(self.viewport().rect(),
                         Qt.AlignCenter, elided_text)
        painter.restore()

    def set_info_text(self, text):
        self.placeholder_text = text

    def update_table(self, dataframes):
        self.clear()

        self.setRowCount(int(len(dataframes) / 2))
        self.setColumnCount(4)

        row = 0
        col = 0
        for key, value in dataframes.items():
            self.setItem(
                int(row), (col % 2) * 2, QTableWidgetItem(str(key)))
            self.setItem(
                int(row), (col % 2) * 2 + 1, QTableWidgetItem(str(value)))
            row += 0.5
            col += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)

    table_widget = InfoTable()
    table_widget.update_table(dataframes)

    table_widget.show()
    sys.exit(app.exec_())
