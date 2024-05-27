from qt_material import apply_stylesheet

MAIN_COLOR = {
    # Font
    "font-size": '20px',
    "primaryColor": '#009688',
    "primaryLightColor": '#52c7b8',
    "secondaryColor": '#f5f5f5',
    "secondaryLightColor": '#ffffff',
    "secondaryDarkColor": '#E6E6E6',
    "primaryTextColor": '#000000',
    "secondaryTextColor": '#000000'
}

MY_SUB_GRAY_COLOR = "rgba(160, 160, 160, 1)"


def rgba_to_string_and_convert(color_string):
    # color_string은 "rgba(r, g, b, a)" 형식이라고 가정합니다. 여기서 r, g, b는 0에서 255 사이의 정수이고, a는 0에서 1 사이의 부동 소수점 숫자입니다.
    # "rgba(r, g, b, a)"를 파싱하여 r, g, b, a 값을 추출합니다.
    rgba_values = color_string.replace(
        "rgba(", "").replace(")", "").split(",")
    r, g, b, a = map(float, rgba_values)

    # 각 색상 값을 16진수로 변환합니다.
    hex_r = format(int(r), '02x')
    hex_g = format(int(g), '02x')
    hex_b = format(int(b), '02x')
    hex_color = f"#{hex_r}{hex_g}{hex_b}"

    # decimal_a = int(a * 255)
    # decimal_color = f"rgba({int(r)}, {int(g)}, {int(b)}, {decimal_a / 255})"

    return f"{hex_color}"


# 줄바꿈을 변경해서는 안됩니다.
def apply_theme(app, font_size):
    apply_stylesheet(app, theme='light_teal_500.xml',
                     invert_secondary=True, extra=MAIN_COLOR)

    mycolor = MY_SUB_GRAY_COLOR
    mycolor_16 = rgba_to_string_and_convert(mycolor)

    ss = app.styleSheet()
    ss = ss.replace("""  font-family: Roboto;

  
    font-size: 13px;""", """  font-family: Roboto;

  
    font-size: """ + str(font_size) + """px;""")
    ss = ss.replace("""QPushButton:disabled {
  color: rgba(255, 255, 255, 0.75);
  background-color: transparent;
  border-color:  #ffffff;
}""", """QPushButton:disabled {
  color: """ + mycolor + """;
  background-color: transparent;
  border-color:  #ffffff;
}""")
    ss = ss.replace("""QPushButton:disabled {
  border: 2px solid rgba(255, 255, 255, 0.75);
}""", """QPushButton:disabled {
  border: 1px solid """ + mycolor + """;
}""")
    ss = ss.replace("""QTableView {
  background-color: #E6E6E6;
  border: 1px solid #f5f5f5;
  border-radius: 4px;
}""", """QTableView {
  background-color: #E6E6E6;
  border: 1px solid """ + mycolor_16 + """;
  border-radius: 4px;
}""")
    ss = ss.replace("""QListView {
  border-radius: 4px;
  padding: 4px;
  margin: 0px;
  border: 0px;
}""", """QListView {
  border-radius: 4px;
  padding: 4px;
  margin: 0px;
  border: 1px solid """ + mycolor + """;
}""")
    # 스크롤바 : 색 더 진하게
    ss = ss.replace("""QScrollBar::handle {
  background: rgba(0, 150, 136, 0.1);
}""", """QScrollBar::handle {
  background: rgba(0, 150, 136, 0.3);
}""")
    # 그룹박스
    ss = ss.replace("""QGroupBox,
QFrame {
  background-color: #E6E6E6;
  border: 2px solid #ffffff;
  border-radius: 4px;
}""", """QGroupBox,
QFrame {
  background-color: #E6E6E6;
  border: 1px solid """ + mycolor + """;
  border-radius: 4px;
}""")
    ss = ss.replace("""QGroupBox::title {
  color: rgba(0, 0, 0, 0.4);
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 16px;
  background-color: #E6E6E6;
  background-color: transparent;
  height: 36px;
}""", """QGroupBox::title {
  color: rgba(0, 0, 0, 0.9);
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 16px;
  background-color: #E6E6E6;
  background-color: transparent;
  height: 36px;
}""")
    app.setStyleSheet(ss)

    # print(ss)