import requests
from bs4 import BeautifulSoup
import json
import time
from time import sleep
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


def get_station_info(naver_code):
    base_query = "https://pts.map.naver.com/end-subway/ends/web/{naver_code}/home".format(naver_code=naver_code)
    page = requests.get(base_query)
    soup = BeautifulSoup(page.text, "html.parser")
    try:
        line_num = soup.select_one(
            'body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.line_no').get_text()
        station_nm = soup.select_one(
            'body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.place_name').get_text()
    except:
        return None

    return {"station_nm": station_nm, "naver_code": naver_code, "line_num": line_num}


def find_code():
    with Pool(6) as p:
        codes = range(100, 20000)
        results = list(tqdm(p.imap_unordered(get_station_info, codes), total=len(codes), desc='Processing'))

    INFO = {}
    for result in results:
        if result is None:
            continue

        line_num = result["line_num"]
        station_nm = result["station_nm"]
        naver_code = result["naver_code"]

        if line_num not in INFO:
            INFO[line_num] = []

        block = {"station_nm": station_nm, "naver_code": naver_code}
        INFO[line_num].append(block)

    return INFO


if __name__ == "__main__":
    start = time.time()
    with open('subway_information.json', 'w', encoding='utf-8') as f:
        json.dump(find_code(), f, ensure_ascii=False, indent=4)
    end = time.time()
    print(f"{end - start:.5f} sec")
