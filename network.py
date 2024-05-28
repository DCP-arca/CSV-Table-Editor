import requests
from urllib.parse import quote

URL_ADDR = "https://api.vworld.kr/req/address"
URL_PNU = "https://api.vworld.kr/req/data?service=data&request=GetFeature&attrFilter=pnu:=:{pnu}&data=LP_PA_CBND_BUBUN&key={apikey}"
URL_MAP = "https://api.vworld.kr/req/image"

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


def get_map_img(api_key, epsg, zoom=18, width=1024, height=1024, basemap="PHOTO_HYBRID"):
    x = epsg[0]
    y = epsg[1]

    zoom = min(max(zoom, 6), 18)

    params = {
        "service": "image",
        "request": "getmap",
        "key": api_key,
        "format": "png",
        "basemap": basemap,
        "center": f"{x},{y}",
        "zoom": zoom,
        "size": f"{width},{height}",
        "marker": f"point:{x} {y}|image:img09"
    }

    res = requests.get(URL_MAP, params=params)

    return res.status_code == 200, res.content


if __name__ == '__main__':
    apikey = ""
    pnu = "4377034032102800000"

    l, b = get_mapinfo_from_pnu(apikey, pnu)
    if not b:
        print("error")
    else:
        iss, pm = get_static_map(apikey, b)

        print(l, b)
        print(iss)
        print(type(pm))
        print(len(pm))
