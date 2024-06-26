import os
import re

import pandas as pd
import numpy as np
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
        try:
            first_line = next(file)
        except Exception as e:
            print(e)
            return ""
    return first_line


def remove_special_characters(text):
    # 정규 표현식을 사용하여 특수문자를 제거
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return clean_text


class DataEditType:
    EDIT_VALUE = 0
    ADD_COLUMN = 1
    ADD_ROW = 2
    DUPLICATE_COLUMN = 3
    DUPLICATE_ROW = 4
    REMOVE_COLUMN = 5
    REMOVE_ROW = 6
    EDIT_COLUMN = 7
    EDIT_ROW = 8


class DataManager:
    def __init__(self, parent):
        self.parent = parent
        self.data = None
        self.cond_data = None
        self.now_conditions = []
        self.edited_list = []
        self.is_dbf_loaded = False

    def is_already_loaded(self):
        return (self.data is not None)

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
                    if not first_line:
                        return ERRORCODE_LOAD.CSV_FAIL
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
        self.cond_data = self._create_copied_data()
        self.now_conditions = []
        self.edited_list = []
        self.is_dbf_loaded = src.endswith(".dbf")

        return ERRORCODE_LOAD.SUCCESS

    def _create_copied_data(self):
        copied_data = self.data.copy(deep=True)
        copied_data.replace('', np.nan, inplace=True)
        copied_data.fillna(np.nan, inplace=True)

        return copied_data

    def change_value(self, row, col, value):
        target_df = self.cond_data.iloc[row].copy()
        target_df[col] = value
        self.cond_data.iloc[row] = target_df

        self.edited_list.append(
            [DataEditType.EDIT_VALUE, [row, col, value]])

    def change_hv(self, edit_type: DataEditType, args):
        self.cond_data = self._change_hv_func(self.cond_data, edit_type, args)

        self.edited_list.append([edit_type, args])

    # it's static
    # 변경 사항이 있으면 달라진 df를 return한다. 그 이외의 경우, 그대로 return 한다.
    def _change_hv_func(__self, df, edit_type, args):
        if edit_type == DataEditType.ADD_COLUMN:
            df.insert(args[0], args[1], "")
        elif edit_type == DataEditType.ADD_ROW:
            new_row = pd.Series([""] * df.shape[1], index=df.columns)
            insert_index = args[0]
            df = pd.concat([df.iloc[:insert_index], pd.DataFrame(
                [new_row]), df.iloc[insert_index:]]).reset_index(drop=True)
        elif edit_type == DataEditType.DUPLICATE_COLUMN:
            col_name = df.columns[args[0]]
            new_name = col_name[:]
            while new_name in df:
                new_name = "_" + new_name
            df.insert(args[0], new_name, df[col_name])
        elif edit_type == DataEditType.DUPLICATE_ROW:
            duplicated_row = df.iloc[args[0]].copy()  # 지정한 행을 복제
            insert_index = args[0]
            df = pd.concat([df.iloc[:insert_index], pd.DataFrame(
                [duplicated_row]), df.iloc[insert_index:]]).reset_index(drop=True)
        elif edit_type == DataEditType.REMOVE_COLUMN:
            col_name = df.columns[args[0]]
            df.drop(columns=[col_name], inplace=True)
            df.reset_index(drop=True, inplace=True)
        elif edit_type == DataEditType.REMOVE_ROW:
            df.drop(index=args[0], inplace=True)
            df.reset_index(drop=True, inplace=True)
        elif edit_type == DataEditType.EDIT_COLUMN:
            target_column_index = int(args[0])
            coppied_column_index = int(args[1])
            df.iloc[:, target_column_index] = df.iloc[:, coppied_column_index]
        elif edit_type == DataEditType.EDIT_ROW:
            target_index = args[0]
            value_list = args[1]

            for i, value in enumerate(value_list):
                if i < len(df.columns):
                    df.iat[target_index, i] = value
                else:
                    break

            # 나머지 값을 빈 문자열("")로 대체
            for i in range(len(value_list), len(df.columns)):
                df.at[target_index, i] = ""

        return df

    def change_condition(self, conditions):
        sel, is_success = self._create_series_by_condition(conditions)

        if is_success:
            # 성공시에만 저장.
            self.cond_data = self._create_copied_data()
            self.cond_data = self.cond_data[sel]
            self.now_conditions = conditions
            return True

        return False

    def sort(self, column_name, sort_mode):
        try:
            if sort_mode == ENUM_TABLEVIEW_SORTMODE.ASCEND:
                self.cond_data = self.cond_data.sort_values(
                    by=column_name, ascending=True, na_position='last')  # , key=key_func)
            elif sort_mode == ENUM_TABLEVIEW_SORTMODE.DESCEND:
                self.cond_data = self.cond_data.sort_values(
                    by=column_name, ascending=False, na_position='last')  # , key=key_func)
            elif sort_mode == ENUM_TABLEVIEW_SORTMODE.ORIGINAL:
                self.cond_data = self.cond_data.sort_index()
        except Exception as e:
            print(e)
            return False

        return True

    def _create_series_by_condition(self, conditions):
        sel = pd.Series([True] * len(self.data))

        cond_data = self._create_copied_data()

        for cond in conditions:
            fs = FilterStruct(datastr=cond)

            if fs.is_minmax_mode:
                try:
                    result_float = cond_data[fs.column].astype(float)
                except Exception as e:
                    print(e)
                    return None, False

                sel &= (result_float >= float(fs.min_val)) & (
                    result_float <= float(fs.max_val))
            else:
                sel &= self.data[fs.column].str.contains(
                    fs.str_val)

        return sel, True

    # now_conditions을 기반으로 select를 붙이고 dst를 내보냄
    # 체크모드가 아니라면 cond_data를 직접 내보내지 마시오. sort에 영향을 받음.
    def export(self, dst, sep_mode, list_target_column, select_mode, list_checked):
        result = self.data.copy(deep=True)

        # change value
        for value_list in self.edited_list:
            detype = value_list[0]
            args = value_list[1]

            if detype == DataEditType.EDIT_VALUE:
                row = args[0]
                col = args[1]
                value = args[2]

                target_df = result.iloc[row].copy()
                target_df[col] = value
                result.iloc[row] = target_df
            else:
                result = self._change_hv_func(result, detype, args)

        # option 1. 분리자 설정
        sep = "," if sep_mode == ENUM_SEPERATOR.COMMA else "|"

        # option 2. 행 거르기 or select 추가하기
        if select_mode == ENUM_SAVE_ROW.ALL:
            pass
        elif select_mode == ENUM_SAVE_ROW.FILTERED:
            sel, _ = self._create_series_by_condition(self.now_conditions)
            result = result[sel]
        elif select_mode == ENUM_SAVE_ROW.FILTERED_SELECT:
            sel, _ = self._create_series_by_condition(self.now_conditions)
            result["select"] = pd.Series(sel).astype(int)
        elif select_mode == ENUM_SAVE_ROW.CHECKED:
            list_checked_df = []
            for index in list_checked:
                list_checked_df.append(result.iloc[index])
            result = pd.concat(list_checked_df)
        elif select_mode == ENUM_SAVE_ROW.CHECKED_SELECT:
            sel = pd.Series([False] * len(result))
            sel.iloc[list_checked] = True
            result["select"] = pd.Series(sel).astype(int)

        # option 3. 열(라벨) 거르기
        if list_target_column:
            result = result[list_target_column]

        if self.is_dbf_loaded:
            # TODO write dbf
            fd = FileIODialog(
                "csv 파일을 쓰는 중입니다.",
                lambda: result.to_csv(dst,
                                      sep=sep,
                                      index=False,
                                      encoding="euc-kr"))
        else:
            fd = FileIODialog(
                "csv 파일을 쓰는 중입니다.",
                lambda: result.to_csv(dst,
                                      sep=sep,
                                      index=False,
                                      encoding="euc-kr"))

        if fd.exec_() != QDialog.Accepted:
            return False

        return True
