import pandas as pd
import os

dict_code_table = {
    "STDMT": "기준월",
    "PNU": "토지코드",
    "LAND_SEQNO": "토지일련번호",
    "SGG_CD": "시군구코드",
    "LAND_LOC_CD": "토지소재지코드",
    "LAND_GBN": "토지구분",
    "BOBN": "본번",
    "BUBN": "부번",
    "ADM_UMD_CD": "행정읍면동코드",
    "PNILP": "공시지가",
    "CMPR_PJJI_NO1": "",
    "CMPR_PJJI_NO2": "",
    "LAND_GRP": "",
    "BSIN_AREA": "",
    "JIMOK": "지목",
    "ACTL_JIMOK": "",
    "PAREA": "면적",
    "SPFC1_AREA": "",
    "SPFC2_AREA": "",
    "SPFC1": "용도지역1",
    "SPFC2": "용도지역2",
    "SPCFC": "",
    "RSTA_ETC": "",
    "RSTA_AREA_RATE": "",
    "RSTA_ETC21": "",
    "RSTA_ETC22": "",
    "RSTA2_USE_YN": "",
    "RSTA2_AREA_RATE": "",
    "RSTA_UBPLFC1": "",
    "CFLT_RT1": "",
    "RSTA_UBPLFC2": "",
    "CFLT_RT2": "",
    "FARM_GBN": "농지구분",
    "FRTL": "",
    "LAND_ADJ": "",
    "FRST1": "임야1",
    "FRST2": "임야2",
    "LAND_USE": "토지이용상황",
    "LAND_USE_ETC": "토지용도기타",
    "GEO_HL": "지형고저",
    "GEO_FORM": "지형형상",
    "GEO_AZI": "지형방위",
    "ROAD_SIDE": "도로접면",
    "ROAD_DIST": "도로거리",
    "HARM_RAIL": "유해시설철도",
    "HARM_WAST": "유해시설기타",
    "LCLW_MTHD_CD": "",
    "LCLW_STEP_CD": "",
    "HANDWK_YN": "",
    "PY_JIGA": "종전지가",
    "PREV_JIGA": "전년지가",
    "CALC_JIGA": "산정지가",
    "VRFY_JIGA": "검증지가",
    "READ_JIGA": "열람지가",
    "OPN_SMT_JIGA": "",
    "FOBJCT_JIGA": "",
    "PY2_JIGA": "2년전지가",
    "PY3_JIGA": "3년전지가",
    "PY4_JIGA": "4년전지가",
    "OWN_GBN": "소유구분",
    "OWN_TYPE": "소유형태",
    "EXAMER_OPN_CD": "조사가의견코드",
    "REV_CD": "심의코드",
    "EXAMER_CD": "조사자코드",
    "CNFER_CD": "확인자코드",
    "VRFY_GBN": "검증대상필지구분",
    "PY_VRFY_GBN": "전년검증대상필지구분",
    "LAND_MOV_YMD": "",
    "LAND_MOV_RSN_CD": "",
    "HOUSE_PANN_YN": "",
    "SPCFC2": "",
    "RSTA_ETC2": "",
    "LAND_USE_SOLAR": "",
    "LAND_CON": "경지정리",
    "DUP_AREA_RATE": "",
    "GRAVE_GBN": "",
    "GRAVE_AREA_RATE": "",
    "HARM_SUBSTATION": "",
    "GTX_GBN": "",
    "PJJI_DIST1": "",
    "PJJI_DIST2": "",
    "DIFF_CD": "",
    "COL_ADM_SECT_CD": "원천시군구코드"
}


def remove_extension(file_path):
    base = os.path.splitext(file_path)[0]
    return base


class CSVLabelAdder:
    def load(self, src):
        parquet_name = remove_extension(src) + ".parquet"
        if not os.path.isfile(parquet_name):
            df = pd.read_csv(src, encoding="euc-kr", sep="|", dtype=object)
            df.to_parquet(parquet_name)

        self.data = pd.read_parquet(parquet_name)

    def select(self, name, min1, max1):
        d = self.data[name].astype("float")
        self.sel = (min1 <= d) & (d <= max1)

    def return_select(self):
        return self.data[self.sel]

    def add_and_save(self, dst):
        result = self.data.copy(deep=True)

        result["select"] = pd.Series(self.sel).astype(int)

        result.to_csv(dst,
                      sep='|',
                      index=False,
                      encoding="euc-kr")


if __name__ == "__main__":
    a = CSVLabelAdder()
    a.load("test_target.csv")
    a.select("PNILP", 40000, 41000)
    print(len(a.data))
    print(type(a.sel))
    # a.add_and_save("result.csv")
