import requests
from bs4 import BeautifulSoup
import json
import time
from time import sleep
from multiprocessing import Pool, cpu_count
import boto3


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
        results = p.map(get_station_info, codes)

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



def upload_file_to_s3(bucket_name, key, file_path):
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(file_path, bucket_name, key)
    return True


def download_data_from_s3(bucket_name, key, download_path):
    s3 = boto3.resource('s3')
    # 다운로드 후에 어디에다가 위치시킬 것인지 경로
    bucket = s3.Bucket(bucket_name)
    objects = list(bucket.objects.filter(Prefix=key))
    if objects and objects[0].key == key:
        bucket.download_file(objects[0].key, download_path)
        return True
    return False


def delete_file_in_s3(bucket_name, key):
    s3 = boto3.resource('s3')
    s3.meta.client.delete_object(Bucket=bucket_name, Key=key)
    return True




# handler
def handler(event, context):
    # 크롤링 후 json 파일 생성
    file = '/tmp/subway_information.json'
    with open(file, 'w', encoding='utf-8') as f:
            json.dump(find_code(), f, ensure_ascii=False, indent=4)

    # 버킷에 저장 준비
    bucket_name = "bucketestmy"
    key = "bmt/subway_information.json"
    file_path = "/tmp/subway_information.json" # lambda에서는 파일을 /tmp/에 저장

    s3 = boto3.client('s3')

    result = upload_file_to_s3(bucket_name, key, file_path)

    if result:
        return {
            'statusCode': 200,
            'body': json.dumps("upload success")
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps("upload fail")
        }
