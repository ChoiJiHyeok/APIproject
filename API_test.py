import requests
import xmltodict as xmltodict
import math
import time

content = []

stat_time = time.time()
key = 'cbbbb410eb3d4bfa88e79a9172862f'
url = f'http://www.incheon.go.kr/dp/openapi/data?apicode=10&page=1&key={key}'
data_total = int(xmltodict.parse(requests.get(url).content)['data']['totalCount'])
total_page = math.ceil(data_total/10)
for page in range(1, total_page+1):
    url = f'http://www.incheon.go.kr/dp/openapi/data?apicode=10&page={page}&key={key}'
    content = requests.get(url).content
    dict = xmltodict.parse(content)
    data = dict['data']
    data_page = data['page']
    date_item = data['list']['item']
    for i in date_item:
        data_listnum = i['listNum']
        data_year = i['histYear']
        data_month = i['histDate'][0]+i['histDate'][1]
        data_day=i['histDate'][2]+i['histDate'][3]
        date_summary = i['summary']
        print(f'등록 NO: {data_listnum}, '
              f'일자: {data_year}년 {data_month}월 {data_day}일, '
              f'내용: {date_summary}')
end_time = time.time()

print(end_time-stat_time)