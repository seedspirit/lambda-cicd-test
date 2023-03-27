import requests
from bs4 import BeautifulSoup
import json
import boto3
import os

# 네이버 시간표 복사하는 find_code 함수
def find_code():
    INFO = {}

    for naver_code in range(100, 400):
        base_query = "https://pts.map.naver.com/end-subway/ends/web/{naver_code}/home".format(naver_code=naver_code)
        page = requests.get(base_query)
        soup = BeautifulSoup(page.text, "html.parser")
        try:
            line_num = soup.select_one('body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.line_no').get_text()
            station_nm = soup.select_one('body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.place_name').get_text()
        except:
            continue

    # 호선 자체가 새로 생기는 경우가 있을 것 같아 호선을 미리 정의하지 않고, 크롤링 결과에 의해 정의되게 함
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
def lambda_handler(event, context):
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