# encoding:utf-8
from bs4 import BeautifulSoup
import traceback
import requests
from eng2chs import readip
import sqlite3
from sqlite3 import IntegrityError
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import cgitb
from fake_useragent import UserAgent
from retrying import retry
import time
import chardet
try:
    ua = UserAgent()
except:
    ua = UserAgent()
conn = sqlite3.connect(r'data.db')

@retry(stop_max_attempt_number=10)
def req(url, headers, cookie=None):
    # proxies = getproxy()

    res = requests.get(url=url, headers=headers, timeout=500)
    return res

if __name__ == '__main__':
    ua = UserAgent()
    c = conn.cursor()
    sql = 'SELECT * FROM digi'
    alist = c.execute(sql).fetchall()
    for item in alist[25:]:
        # refer = 'https://www.digikey.cn/products/zh/sensors-transducers/sensor-cable-accessories/949?pageNumber='
        num = item[3].split('/')[-1]
        subcate = item[1].replace('\xa0','').replace(' ','').replace(',','')
        match = re.search(r'\d+项',subcate)
        start,end = match.regs[0]
        total = int(subcate[start:end-1])
        subcate = subcate[:-len(str(total))-3]
        pages = int(total/25) + 1

        title = item[0] + ' - ' + subcate
        title = title.replace('/','&')
        f = open('E:\\digidata\\%s.csv'%title,'w',encoding='utf-8')

        for i in range(pages):
            if i == 0:
                page = ''
            else:
                page = str(i+1)

            #refer和url相对应
            refer = 'https://www.digikey.cn%s?pageNumber=%s' % (item[3], page)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                       'Referer': refer,
                       'sec-fetch-mode': 'navigate',
                       'sec-fetch-site': 'none',
                       'sec-fetch-user': '?1',
                       'upgrade-insecure-requests': '1'}

            url = 'https://www.digikey.cn%sAdvancedSearchResultsDownload?&pageNumber=%s&sort=&sortDescending=0&sortType=S&qtyRequested=&c=%s' % (item[3][:-len(num)],page,num)
            res = req(url,headers)
            text = res.content.decode('utf-8')

            if i == 0:
                dlist = text.split('\n')
            else:
                dlist = text.split('\n')[1:]
            for d in dlist:
                f.write(d+'\r')
            print('%s %s页\t完成'%(title,page))
            time.sleep(2)
        f.close()
        print(title+'\t完成')
        time.sleep(5)
