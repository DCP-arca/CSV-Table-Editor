import pandas as pd
import pyperclip
import re

REG_TAG = r"^CSVTE_(column|row)\[(.+?)\]$"


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def clipboard_copy_csvte_info(df, key, is_column):
    if is_column:
        result = f"CSVTE_column[{key}]"
        pyperclip.copy(result)
    else:
        values_str = ', '.join(map(str, df.iloc[key]))
        result = f"CSVTE_row[{values_str}]"
        pyperclip.copy(result)


def clipboard_paste_csvte_info():
    csvte_str = pyperclip.paste()

    result = None
    reg_result = re.match(REG_TAG, csvte_str)
    if reg_result:
        is_column = reg_result.group(1) == "column"
        result = reg_result.group(2).split(
            ",") if not is_column else reg_result.group(2)

        if is_column and not is_float(result):
            result = None

    return is_column, result


if __name__ == "__main__":
    data = {
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'C': [7, 8, 9]
    }
    df = pd.DataFrame(data, index=['X', 'Y', 'Z'])

    try:
        clipboard_copy_csvte_info(df, 2, True)  # 열을 클립보드에 복사
        print(clipboard_paste_csvte_info())
        clipboard_copy_csvte_info(df, 1, False)  # 행을 클립보드에 복사
        print(clipboard_paste_csvte_info())
    except ValueError as e:
        print(e)
