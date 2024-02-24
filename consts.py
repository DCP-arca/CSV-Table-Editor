from dotmap import DotMap

###
#
#   상수 == Consts에 보관, UPPERCASE
#
#   ClassName == PascalCase
#   file_name == snake_case
#   PyQt5 Function == camelCase
#   function == snake_case
#   variable == snake_case
#
###

ENUM_SEPERATOR = DotMap(
    VERTICAL_BAR=0,
    DOT=1
)

ENUM_LOAD_MODE = DotMap(
    NEW=0,
    APPEND=1,
    ADDROW=2
)

ENUM_SAVE_COLUMN = DotMap(
    ALL=0,
    SELECTED=1
)

ENUM_SAVE_ROW = DotMap(
    ALL=0,
    FILTERED=1,
    FILTERED_SELECT=2,
    CHECKED=3,
    CHECKED_SELECT=4
)

ENUM_TABLEVIEW_SORTMODE = DotMap(
    ASCEND=0,
    DESCEND=1,
    ORIGINAL=2
)

ENUM_TABLEVIEW_INITMODE = DotMap(
    LOAD=0,
    SORT=1,
    CONDITION=2
)

ERRORCODE_LOAD = DotMap(
    SUCCESS=0,
    CANCEL=1,
    CSV_FAIL=2,
    PARQUET_FAIL=3,
    NOT_FOUND_PNU=4
)

SAVE_KEY_MAP = DotMap(
    PARQUET_FILE_ORIGINAL_SIZE="PFOS_",
    OPTION_APIKEY="OPTION_APIKEY",
    OPTION_CLIENTID="OPTION_CLIENTID",
    OPTION_CLIENTSECRET="OPTION_CLIENTSECRET",
    OPTION_FONTSIZE="OPTION_FONTSIZE",  # 9
    OPTION_TABLEPAGESIZE="OPTION_TABLEPAGESIZE"  # 20
)

ENUM_STR_MAP = DotMap(
    STDMT="기준월",
    PNU="토지코드",
    LAND_SEQNO="토지일련번호",
    SGG_CD="시군구코드",
    LAND_LOC_CD="토지소재지코드",
    LAND_GBN="토지구분",
    BOBN="본번",
    BUBN="부번",
    ADM_UMD_CD="행정읍면동코드",
    PNILP="공시지가",
    CMPR_PJJI_NO1="",
    CMPR_PJJI_NO2="",
    LAND_GRP="",
    BSIN_AREA="",
    JIMOK="지목",
    ACTL_JIMOK="",
    PAREA="면적",
    SPFC1_AREA="",
    SPFC2_AREA="",
    SPFC1="용도지역1",
    SPFC2="용도지역2",
    SPCFC="",
    RSTA_ETC="",
    RSTA_AREA_RATE="",
    RSTA_ETC21="",
    RSTA_ETC22="",
    RSTA2_USE_YN="",
    RSTA2_AREA_RATE="",
    RSTA_UBPLFC1="",
    CFLT_RT1="",
    RSTA_UBPLFC2="",
    CFLT_RT2="",
    FARM_GBN="농지구분",
    FRTL="",
    LAND_ADJ="",
    FRST1="임야1",
    FRST2="임야2",
    LAND_USE="토지이용상황",
    LAND_USE_ETC="토지용도기타",
    GEO_HL="지형고저",
    GEO_FORM="지형형상",
    GEO_AZI="지형방위",
    ROAD_SIDE="도로접면",
    ROAD_DIST="도로거리",
    HARM_RAIL="유해시설철도",
    HARM_WAST="유해시설기타",
    LCLW_MTHD_CD="",
    LCLW_STEP_CD="",
    HANDWK_YN="",
    PY_JIGA="종전지가",
    PREV_JIGA="전년지가",
    CALC_JIGA="산정지가",
    VRFY_JIGA="검증지가",
    READ_JIGA="열람지가",
    OPN_SMT_JIGA="",
    FOBJCT_JIGA="",
    PY2_JIGA="2년전지가",
    PY3_JIGA="3년전지가",
    PY4_JIGA="4년전지가",
    OWN_GBN="소유구분",
    OWN_TYPE="소유형태",
    EXAMER_OPN_CD="조사가의견코드",
    REV_CD="심의코드",
    EXAMER_CD="조사자코드",
    CNFER_CD="확인자코드",
    VRFY_GBN="검증대상필지구분",
    PY_VRFY_GBN="전년검증대상필지구분",
    LAND_MOV_YMD="",
    LAND_MOV_RSN_CD="",
    HOUSE_PANN_YN="",
    SPCFC2="",
    RSTA_ETC2="",
    LAND_USE_SOLAR="",
    LAND_CON="경지정리",
    DUP_AREA_RATE="",
    GRAVE_GBN="",
    GRAVE_AREA_RATE="",
    HARM_SUBSTATION="",
    GTX_GBN="",
    PJJI_DIST1="",
    PJJI_DIST2="",
    DIFF_CD="",
    COL_ADM_SECT_CD="원천시군구코드"
)


if __name__ == "__main__":
    print(ENUM_STR_MAP.COL_ADM_SECT_CD)
