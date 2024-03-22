import os
import re

import pandas as pd
from dbfread import DBF

from PyQt5.QtWidgets import QDialog

from consts import SAVE_KEY_MAP, ENUM_LOAD_MODE, ENUM_SEPERATOR, ENUM_SAVE_ROW, ENUM_TABLEVIEW_SORTMODE, ERRORCODE_LOAD
from gui_dialog import FileIODialog
from gui_search import FilterStruct


def remove_extension(file_path):
    base = os.path.splitext(file_path)[0]
    return base


def get_parent_folder(file_path):
    return os.path.dirname(file_path)


def get_first_line_from_file(filename):
    with open(filename, 'r') as file:
        first_line = next(file)
    return first_line


def remove_special_characters(text):
    # 정규 표현식을 사용하여 특수문자를 제거
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return clean_text


class DataManager:
    def __init__(self, parent):
        self.parent = parent
        self.data = None
        self.cond_data = None
        self.now_conditions = []
        self.is_dbf_loaded = False

    def check_parquet_exists(self, src):
        # 파르켓 경로 생성
        parquet_src = remove_extension(src) + ".parquet"

        # 파르켓 존재 체크
        if not os.path.isfile(parquet_src):
            return False

        # 이 파르켓을 만들때 생성했던 원본 사이즈 불러오기
        saved_file_size = self.parent.settings.value(
            SAVE_KEY_MAP.PARQUET_FILE_ORIGINAL_SIZE + remove_special_characters(src), -1)
        if saved_file_size == -1:
            return False

        # 원본 사이즈 체크
        file_size = os.path.getsize(src)
        if file_size != saved_file_size:
            return False

        return True

    # 일단 .parquet파일이 존재하는지 체크, 없다면, csv 파일을 읽고 .parquet을 생성후 그것을 불러옴. 이후 load_mode를 적용함.
    def load_data(self, src, load_mode):
        parquet_name = remove_extension(src) + ".parquet"
        # sep = "," if sep_mode == ENUM_SEPERATOR.COMMA else "|"

        if not self.check_parquet_exists(src):
            # 1. 파일 읽기 준비
            if src.endswith(".dbf"):
                def convert_to_df():
                    dbf = DBF(src, encoding='euc-kr')
                    return pd.DataFrame(iter(dbf))

                loading_dialog = FileIODialog(
                    "dbf 파일을 읽고 있습니다.", convert_to_df)
            else:
                target_sep = ''
                for sep in [',', '|']:
                    first_line = get_first_line_from_file(src)
                    if sep in first_line:
                        target_sep = sep
                        break

                if not target_sep:
                    return ERRORCODE_LOAD.NOT_FOUND_SEP

                loading_dialog = FileIODialog(
                    "csv 파일을 읽고 있습니다.",
                    lambda: pd.read_csv(src, encoding="euc-kr", sep=target_sep, dtype=object))

            # 1. 파일 읽기 실행 및 성공체크
            if loading_dialog.exec_() != QDialog.Accepted:
                return ERRORCODE_LOAD.CANCEL
            df = loading_dialog.result
            if df.empty:
                return ERRORCODE_LOAD.CSV_FAIL

            # 2. .parquet 파일 생성
            loading_dialog = FileIODialog(
                ".parquet 파일을 생성 중입니다.",
                lambda: df.to_parquet(parquet_name))
            if loading_dialog.exec_() != QDialog.Accepted:
                return ERRORCODE_LOAD.CANCEL

            # 2.5. 원본 파일 사이즈 기록
            file_size = os.path.getsize(src)
            self.parent.settings.setValue(
                SAVE_KEY_MAP.PARQUET_FILE_ORIGINAL_SIZE + remove_special_characters(src), file_size)

        # 1 or 3. .parquet 파일 읽기
        loading_dialog = FileIODialog(
            ".parquet 파일을 읽는 중입니다.",
            lambda: pd.read_parquet(parquet_name))
        if loading_dialog.exec_() != QDialog.Accepted:
            return ERRORCODE_LOAD.CANCEL
        new_data = loading_dialog.result
        if new_data.empty:
            return ERRORCODE_LOAD.PARQUET_FAIL

        # 4. load mode에 따른 동작
        if load_mode == ENUM_LOAD_MODE.NEW:
            self.data = new_data
        elif load_mode == ENUM_LOAD_MODE.APPEND:
            self.data = pd.concat([self.data, new_data])
        elif load_mode == ENUM_LOAD_MODE.ADDROW:
            try:
                self.data = pd.merge(self.data, new_data,
                                     on='PNU', how='outer')
            except Exception as e:
                print(e)
                return ERRORCODE_LOAD.NOT_FOUND_PNU

        # 5. 멤버 변수 초기화
        self.cond_data = self.data.copy(deep=True)
        self.now_conditions = []
        self.is_dbf_loaded = src.endswith(".dbf")

        return ERRORCODE_LOAD.SUCCESS

    def change_condition(self, conditions):
        self.cond_data = self.data.copy(deep=True)
        for cond in conditions:
            fs = FilterStruct(datastr=cond)

            if fs.is_minmax_mode:
                try:
                    cond_float = self.cond_data[fs.column].astype(float)
                except Exception as e:
                    print(e)
                    return False
                self.cond_data = self.cond_data[(
                    cond_float >= fs.min_val) & (cond_float <= fs.max_val)]
            else:
                self.cond_data = self.cond_data[self.cond_data[fs.column].str.contains(
                    fs.str_val)]

        # now_conditions는 성공시에만 저장합니다.
        self.now_conditions = conditions
        return True

    def sort(self, column_name, sort_mode):
        def key_func(x):
            return x.astype(float)

        if sort_mode == ENUM_TABLEVIEW_SORTMODE.ASCEND:
            self.data = self.data.sort_values(by=column_name, key=key_func)
            self.cond_data = self.cond_data.sort_values(
                by=column_name, key=key_func)
        elif sort_mode == ENUM_TABLEVIEW_SORTMODE.DESCEND:
            self.data = self.data.sort_values(
                by=column_name, ascending=False, key=key_func)
            self.cond_data = self.cond_data.sort_values(
                by=column_name, ascending=False, key=key_func)
        elif sort_mode == ENUM_TABLEVIEW_SORTMODE.ORIGINAL:
            self.data = self.data.sort_index()
            self.cond_data = self.cond_data.sort_index()

    def _create_series_by_condition(self, target_df):
        sel = pd.Series([True] * len(self.data))

        for cond in self.now_conditions:
            fs = FilterStruct(datastr=cond)

            if fs.is_minmax_mode:
                result_float = target_df[fs.column].astype(float)
                sel &= (result_float >= fs.min_val) & (
                    result_float <= fs.max_val)
            else:
                sel &= target_df[fs.column].str.contains(
                    fs.str_val)
        return sel

    # now_conditions을 기반으로 select를 붙이고 dst를 내보냄
    def export(self, dst, sep_mode, list_target_column, select_mode, list_checked):
        # option 1. 분리자 설정
        sep = "," if sep_mode == ENUM_SEPERATOR.COMMA else "|"

        # option 2. 행 거르기 or select 추가하기
        if select_mode == ENUM_SAVE_ROW.ALL:
            result = self.data.copy(deep=True)
        elif select_mode == ENUM_SAVE_ROW.FILTERED:
            result = self.data.copy(deep=True)
            sel = self._create_series_by_condition(result)
            result = result[sel]
        elif select_mode == ENUM_SAVE_ROW.FILTERED_SELECT:
            result = self.data.copy(deep=True)
            sel = self._create_series_by_condition(result)
            result["select"] = pd.Series(sel).astype(int)
        elif select_mode == ENUM_SAVE_ROW.CHECKED:
            list_checked_df = []
            for index in list_checked:
                list_checked_df.append(self.cond_data.iloc[index])
            result = pd.concat(list_checked_df)
        elif select_mode == ENUM_SAVE_ROW.CHECKED_SELECT:
            result = self.data.copy(deep=True)
            sel = pd.Series([False] * len(self.data))
            sel.iloc[list_checked] = True
            result["select"] = pd.Series(sel).astype(int)

        # option 3. 열(라벨) 거르기
        if list_target_column:
            result = result[list_target_column]

        if self.is_dbf_loaded:
            # TODO write dbf
            FileIODialog(
                "csv 파일을 쓰는 중입니다.",
                lambda: result.to_csv(dst,
                                      sep=sep,
                                      index=False,
                                      encoding="euc-kr")).exec_()
        else:
            FileIODialog(
                "csv 파일을 쓰는 중입니다.",
                lambda: result.to_csv(dst,
                                      sep=sep,
                                      index=False,
                                      encoding="euc-kr")).exec_()
