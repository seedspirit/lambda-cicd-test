import requests
from bs4 import BeautifulSoup
import json
import time
from time import sleep
from multiprocessing import Process, Pipe
import boto3
import os

INFO = {}

def scrape_subway_info(naver_code, conn):
    base_query = f"https://pts.map.naver.com/end-subway/ends/web/{naver_code}/home"
    page = requests.get(base_query)
    soup = BeautifulSoup(page.text, "html.parser")

    try:
        line_num = soup.select_one('body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.line_no').get_text()
        station_nm = soup.select_one('body > div.app > div > div > div > div.place_info_box > div > div.p19g2ytg > div > button > strong.place_name').get_text()
        conn.send((line_num, station_nm, naver_code))
    except:
        conn.send(None)

def find_code(start, end):
    global INFO
    processes = []
    connections = []

    for naver_code in range(start, end):
        parent_conn, child_conn = Pipe()
        p = Process(target=scrape_subway_info, args=(naver_code, child_conn))
        p.start()
        processes.append(p)
        connections.append(parent_conn)

    for i, conn in enumerate(connections):
        res = conn.recv()
        if res is None:
            continue

        print(res)
        line_num, station_nm, naver_code = res

        if line_num not in INFO:
            INFO[line_num] = []

        block = {"station_nm": station_nm, "naver_code": naver_code}
        INFO[line_num].append(block)

    for p in processes:
        p.join()


def run():
    target = [(100,2000),(2001,4000),(4001,6000),(6001,8000),(8001,10000),(10001,12000),(12001,14000),(14001,16000),(16001,18000),(18001,20000)]
    
    for start, end in target:
        find_code(start, end)
    
    global INFO

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
            json.dump(run(), f, ensure_ascii=False, indent=4)

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
