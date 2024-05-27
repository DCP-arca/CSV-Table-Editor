import pandas as pd
import pyperclip


def copy_to_clipboard(df, key, axis):
    if axis == 'column':
        if key in df.columns:
            value = df[key].to_dict()
            result = f"CSVTE_row[{value}]"
            pyperclip.copy(result)
        else:
            raise ValueError(f"Column {key} does not exist in the DataFrame.")

    elif axis == 'row':
        if key in df.index:
            index = df.index.get_loc(key)
            result = f"CSVTE_column[{index}, {key}]"
            pyperclip.copy(result)
        else:
            raise ValueError(f"Row {key} does not exist in the DataFrame.")
    else:
        raise ValueError("Axis must be either 'row' or 'column'.")


# 예제 데이터 프레임 생성
data = {
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
}
df = pd.DataFrame(data, index=['X', 'Y', 'Z'])

# 함수 사용 예제
try:
    copy_to_clipboard(df, 'B', 'column')  # 열을 클립보드에 복사
    copy_to_clipboard(df, 'Y', 'row')  # 행을 클립보드에 복사
except ValueError as e:
    print(e)
