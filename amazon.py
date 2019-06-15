# encoding:utf-8
from bs4 import BeautifulSoup
import urllib
import requests
from eng2chs import readip
import urllib.request
import os
import shutil
from lxml import etree
import chardet
import sqlite3
import base64
from sqlite3 import IntegrityError
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def spider():
    conn = sqlite3.connect(r'D:/anby/Flask/database/blog.db')
    for i in range(1,76):
        url = 'https://www.amazon.cn/s?rh=n%3A658390051%2Cn%3A%21658391051%2Cn%3A658414051&page='+str(i)
        res = req(url)
        if res == 'filed':
            res = req(url)

        html = BeautifulSoup(res.text)
        books = html.find_all('a', attrs={"class": "s-access-detail-page"})
        for book in books:
            link = book.attrs['href']
            # if '_kin_' in link:
            #     link = link.replace('_kin_','_pap_')
            # if 'ref' not in link:
            #     link = link + 'ref=tmm'
            r = req(link)
            h = BeautifulSoup(r.text)
            booklink = h.find_all('a', attrs={"class": 'title-text'})
            if len(booklink) > 0:
                rlink = r'https://www.amazon.cn/' + booklink[0].attrs['href']
            else: 
                continue
            r = req(rlink)
            h = BeautifulSoup(r.text)
            infos = h.find_all('div',attrs={"class":'content'})[0]
            allinfo = []
            lis = infos.find_all('li')

            for li in lis:
                flag = 0
                #信息中无用项过滤
                for t in ['商品尺寸','商品重量','用户评分','商品排名','zg_hssr_rank']:
                    if t not in li.text:
                        pass
                    else:
                        flag += 1
                #包含:为正常信息 且flag为0代表有用信息
                if flag == 0 and ':' in li.text:
                    allinfo.append(li.text.strip())
                    if '条形码' in li.text:
                        isbn = li.text.split(':')[1]
                        assert isinstance(isbn, str) and len(isbn) == 14, 'ISBN有毛病'
                    if 'ASIN' in li.text:
                        itemno = li.text.split(':')[1]

            allinfo = ('\n').join(allinfo).replace('\'','’')
            
            #图书标题 亚马逊个别书名后接括号里内容过长的删去
            title = h.find('span',attrs={"id":'productTitle'}).text.replace('\'','’')
            if '(' in title:
                regs = re.search('\(.+\)',title).regs
                for reg in regs:
                    if reg[1] - reg[0] > 5:
                        title = title[:reg[0]]
            
            #简介部分在iframe中 需使用selenimu动态获取           
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(rlink)
            iframe = driver.find_elements_by_tag_name('iframe')[3]
            driver.switch_to.frame(iframe)  # 最重要的一步
            soup = BeautifulSoup(driver.page_source, "html.parser")
            intro = soup.select('#iframeContent')[0].text
            intro = intro.replace("'",'‘').strip()

            #获取图书价格和当前购买页面链接
            price = h.find_all("span",attrs={"class":'a-size-base a-color-price a-color-price'})[0].text.strip().replace('￥','')
            buy = '亚马逊\t' + price + '元\t' + rlink

            #图书封面
            cover = h.find('img',attrs={"class":'frontImage'}).attrs['src']
            cover = cover.replace('data:image/jpeg;base64,\n','')
            
            #相关推荐书目 按ASIN码存储
            rec = h.find('div',attrs={"class":'similarities-aui-carousel'}).attrs['data-a-carousel-options']
            recs = re.search(r'"id_list".+:"]', rec, re.M | re.I).group(0)[11:-1].split(',')
            for i in range(len(recs)):
                recs[i] = recs[i][1:-2]
            if len(recs) > 10:
                recs = recs[:10]
            recnos = (' ').join(recs)

            c = conn.cursor()
            sql = "select * from abooks"
            id = len(c.execute(sql).fetchall()) + 1
            subno = itemno
            sql = "INSERT INTO abooks ('id','title','intro','isbn','cover','itemno','subno','recnos','infos','buy') \
                  VALUES ('%d','%s', '%s', '%s', '%s', '%s','%s','%s','%s','%s');" \
                  % (id, title.replace('\'', '’'), intro.replace('\'', '’'), isbn, cover, itemno, subno,recnos, allinfo,buy)

            try:
                c.execute(sql)
            except IntegrityError as e:
                if e == 'UNIQUE constraint failed: books.isbn':
                    break
            conn.commit()
            print(title + '   成功')

def getproxy():
    proxy = readip.readip()
    if proxy == 'Failed to get proxies':
        return getproxy()
    return proxy

#num为失败计数 相同链接可请求10次避免未知网络错误
def req(url,num=0):
    proxies = getproxy()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    try:
        res = requests.get(url=url, proxies=proxies, headers =headers, timeout=500)
    except:
        num = num + 1
        if num == 10:
            return 'filed'
        return req(url)
    return res

if __name__ == '__main__':
    spider()
