import pandas as pd
import os
from consts import SAVE_KEY_MAP, CODE_LOAD_MODE, CODE_SEPERATOR, CODE_SAVE_SELECT


def remove_extension(file_path):
    base = os.path.splitext(file_path)[0]
    return base


def convert_conds_to_item(cond):
    cl = cond.split()
    min_val = float(cl[0])
    column_name = cl[2]
    max_val = float(cl[4])

    return min_val, column_name, max_val


class DataManager:
    def __init__(self, parent):
        self.parent = parent
        self.data = None
        self.cond_data = None
        self.now_conditions = []

    def check_parquet_exists(self, src):
        # 파르켓 경로 생성
        parquet_src = remove_extension(src) + ".parquet"

        # 파르켓 존재 체크
        if not os.path.isfile(parquet_src):
            return False

        # 이 파르켓을 만들때 생성했던 원본 사이즈 불러오기
        saved_file_size = self.parent.settings.value(
            SAVE_KEY_MAP.PARQUET_FILE_ORIGINAL_SIZE, -1)
        if saved_file_size == -1:
            return False

        # 원본 사이즈 체크
        file_size = os.path.getsize(src)
        if file_size != saved_file_size:
            return False

        return True

    def load_data(self, src, load_mode, sep_mode):
        parquet_name = remove_extension(src) + ".parquet"
        sep = "." if sep_mode == CODE_SEPERATOR.DOT else "|"

        if not self.check_parquet_exists(src):
            try:
                df = pd.read_csv(src, encoding="euc-kr", sep=sep, dtype=object)
            except Exception as e:
                print(e)
                return False
            df.to_parquet(parquet_name)
            file_size = os.path.getsize(src)
            self.parent.settings.setValue(
                SAVE_KEY_MAP.PARQUET_FILE_ORIGINAL_SIZE, file_size)

        new_data = pd.read_parquet(parquet_name)
        if load_mode == CODE_LOAD_MODE.NEW:
            self.data = new_data
        elif load_mode == CODE_LOAD_MODE.APPEND:
            self.data = pd.concat([self.data, new_data])
        elif load_mode == CODE_LOAD_MODE.ADDLOW:
            # TODO!!!
            pass

        self.cond_data = self.data.copy(deep=True)
        self.now_conditions = []

        return True

    def change_condition(self, conditions):
        self.now_conditions = conditions

        self.cond_data = self.data.copy(deep=True)
        for cond in conditions:
            min_val, column_name, max_val = convert_conds_to_item(cond)
            cond_float = self.cond_data[column_name].astype(float)
            self.cond_data = self.cond_data[(
                cond_float >= min_val) & (cond_float <= max_val)]

    # now_conditions을 기반으로 select를 붙이고 dst를 내보냄
    def export(self, dst, sep_mode, list_target_column, select_mode):
        # option 1. 분리자 설정
        sep = "." if sep_mode == CODE_SEPERATOR.DOT else "|"

        result = self.data.copy(deep=True)
        sel = pd.Series([True] * len(self.data))
        for cond in self.now_conditions:
            min_val, column_name, max_val = convert_conds_to_item(cond)
            sel &= (result[column_name] >= min_val) & (
                result[column_name] <= max_val)

        # option 2. 열(라벨) 거르기
        if list_target_column:
            result = result[list_target_column]

        # option 3. 행 거르기 or select 추가하기
        if select_mode == CODE_SAVE_SELECT.ALL:
            pass
        elif select_mode == CODE_SAVE_SELECT.CHECKED:
            result = result[sel]
        elif select_mode == CODE_SAVE_SELECT.ADD_SELECT:
            result["select"] = pd.Series(sel).astype(int)

        result.to_csv(dst,
                      sep=sep,
                      index=False,
                      encoding="euc-kr")
