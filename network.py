import requests
from urllib.parse import quote

URL_ADDR = "https://api.vworld.kr/req/address"
URL_PNU = "https://api.vworld.kr/req/data?service=data&request=GetFeature&attrFilter=pnu:=:{pnu}&data=LP_PA_CBND_BUBUN&key={apikey}"
URL_MAP = "https://naveropenapi.apigw.ntruss.com/map-static/v2/raster"

MAPLINK_SEED1 = "https://map.kakao.com/link/search/{addr}"
MAPLINK_SEED2 = "https://map.kakao.com/link/roadview/{y},{x}"
MAPLINK_SEED3 = "https://map.naver.com/p/search/{addr}"

ADD_PARAMS = {
    'service': 'address',
    'request': 'getAddress',
    'version': '2.0',
    'crs': 'epsg:4326',
    'type': 'both',
    'zipcode': 'true',
    'simple': 'false'
}


def get_addr_from_epsg(apikey, epsg):
    params = ADD_PARAMS.copy()

    params['point'] = str(epsg[0]) + "," + str(epsg[1])
    params['key'] = apikey

    response = requests.get(URL_ADDR, params=params)

    # 응답 상태 코드 확인
    if response.status_code == 200:
        import json
        j = json.loads(response.text)
        try:
            return j['response']['result'][0]['text']
        except Exception as e:
            print(f"검색 실패, {str(j)}")
    else:
        print(f"API 요청 실패: {response.status_code}")

    # 예외 처리 및 오류 메시지 출력
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 에러 발생: {e}")
    except Exception as e:
        print(f"오류 발생: {e}")

    return ""


def get_mapinfo_from_pnu(apikey, pnu):
    try:
        response = requests.get(URL_PNU.format(apikey=apikey, pnu=pnu))
        response.raise_for_status()  # 만약 에러가 발생하면 예외를 발생시킵니다.
        json_data = response.json()  # JSON 형식으로 응답을 파싱합니다.

        addr = json_data["response"]["result"]["featureCollection"]["features"][0]["properties"]["addr"]
        bbox = json_data["response"]["result"]["featureCollection"]["bbox"]
        x, y = bbox[0], bbox[1]

        maplink1 = MAPLINK_SEED1.format(addr=quote(addr))
        maplink2 = MAPLINK_SEED2.format(x=x, y=y)
        maplink3 = MAPLINK_SEED3.format(addr=quote(addr))

    except Exception as e:
        print("HTTP 요청 중 에러가 발생했습니다:", e)
        return [], []

    return [addr, maplink1, maplink2, maplink3], [str(x), str(y)]


###
# 로그인 ::: https://www.ncloud.com/product/applicationService/maps
# API ::: https://api.ncloud-docs.com/docs/ai-naver-mapsstaticmap-raster
###
def get_map_img(c_id, c_sec, epsg):
    lon, lat = epsg[0], epsg[1]

    # 좌표 (경도, 위도)
    headers = {
        "X-NCP-APIGW-API-KEY-ID": c_id,
        "X-NCP-APIGW-API-KEY": c_sec,
    }
    # 중심 좌표
    _center = f"{lon},{lat}"
    # 줌 레벨 - 0 ~ 20
    _level = 16
    # 가로 세로 크기 (픽셀)
    _w, _h = 500, 300
    # 지도 유형 - basic, traffic, satellite, satellite_base, terrain
    _maptype = "satellite"
    # 반환 이미지 형식 - jpg, jpeg, png8, png
    _format = "png"
    # 고해상도 디스펠레이 지원을 위한 옵션 - 1, 2
    _scale = 1
    # 마커
    _markers = f"""type:d|size:mid|pos:{lon} {lat}|color:red"""
    # 라벨 언어 설정 - ko, en, ja, zh
    _lang = "ko"
    # 대중교통 정보 노출 - Boolean
    _public_transit = True
    # 서비스에서 사용할 데이터 버전 파라미터 전달 CDN 캐시 무효화
    _dataversion = ""

    # URL
    url = f"{URL_MAP}?center={_center}&level={_level}&w={_w}&h={_h}&maptype={_maptype}&format={_format}&scale={_scale}&markers={_markers}&lang={_lang}&public_transit={_public_transit}&dataversion={_dataversion}"
    res = requests.get(url, headers=headers)

    return res.status_code == 200, res.content


if __name__ == '__main__':
    apikey = ""
    pnu = "4377034032102800000"

    client_id = ""
    client_secret = ""

    l, b = get_mapinfo_from_pnu(apikey, pnu)
    if not b:
        print("error")
    else:
        iss, pm = get_map_img(client_id, client_secret, b)

        print(l, b)
        print(iss)
        print(type(pm))
        print(len(pm))
