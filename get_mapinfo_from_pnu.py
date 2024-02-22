import requests
from urllib.parse import quote

URL = "https://api.vworld.kr/req/data?service=data&request=GetFeature&attrFilter=pnu:=:{pnu}&data=LP_PA_CBND_BUBUN&key={apikey}"

MAPLINK_SEED1 = "https://map.kakao.com/link/search/{addr}"
MAPLINK_SEED2 = "https://map.kakao.com/link/roadview/{y},{x}"
MAPLINK_SEED3 = "https://map.naver.com/p/search/{addr}"


def get_mapinfo_from_pnu(apikey, pnu):
    try:
        response = requests.get(URL.format(apikey=apikey, pnu=pnu))
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
        return None

    return [addr, maplink1, maplink2, maplink3]


if __name__ == '__main__':
    apikey = "A65F7069-061D-378F-B2D1-5E635A17BA43"
    pnu = "4377034032102800000"
    print(get_mapinfo_from_pnu(apikey, pnu))
