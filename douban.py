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

def spider():
    conn = sqlite3.connect(r'D:/anby/Flask/database/blog-1.db')
    for i in range(0,55):
        num = i * 20
        url = r'https://book.douban.com/tag/%E7%BC%96%E7%A8%8B?start=' + str(num) + '&type=T'
        res = req(url)
        if res == 'filed':
            res = req(url)
                
        html = BeautifulSoup(res.text)
        lis = html.find_all('li', attrs={"class": "subject-item"})
                
        for li in lis:
            a = li.contents[3].contents[1].contents[1]
            link = a.get('href')
            subno = link.split('/')[-2]
            title = a.text.replace('\n','')
            if is_contain_chinese(title):
                title = title.replace(':','：').replace(' ', '')
            else:
                title = title.replace(':', '：').strip()
            r = req(link)
            if r == 'filed':
                print(title + '   不行')
                continue

            h = BeautifulSoup(r.text)
            intro = ''
            cover = h.find_all('a',attrs = {"class":"nbg"})[0].attrs['href']

            buy = []
            try:
                buys = h.find_all('ul', attrs={"class": "more-after"}) #购买列表
                ifbuys = 1
            except:
                ifbuys = 0
            if ifbuys == 1:
                for b in buys:
                    mer = b.find_all('li')  #merchant 遍历商家
                    binfo = ''
                    for m in mer:
                        a = m.find_all('a')
                        if len(a) == 2:
                            site = a[0].text.strip()
                            price = a[1].text.strip()
                        else:
                            text = a[0].text.strip().split('\n\n')
                            if len(text)>1:
                                site = text[0]
                                price = text[1]
                            else:
                                continue
                        blink = a[0].attrs['href']
                        binfo = site + '\t' + price + '\t' + blink
                        if binfo != '':
                            buy.append(binfo)
                if buy != []:
                    buy = ('\n').join(buy)
                else:
                    buy = ''
                        
            try:
                intro = h.find_all('div', attrs={"class": "intro"})[0].text.strip()
                if is_contain_chinese(title):
                    intro = h.find_all('div',attrs={"class":"intro"})[0].text.replace(' ','')
            except:
                pass
            infos = h.find_all('span',attrs = {"class":"pl"})
            allinfo = []
            for info in infos:
                if info.next == 'ISBN:':#isbn单独抽取
                    isbn = info.next_sibling.strip()
                try:
                    if(info.next_sibling.strip() not in ['',' ','\n',':']):
                        allinfo.append(info.next + info.next_sibling.strip())
                except:
                    break  #报错说明到底直接跳出
            allinfo = ('\n').join(allinfo).replace('\'','’') #英文 "'" 符号导致字符串中断 数据库无法插入

            tags = h.find_all('a',attrs = {"class":"tag"})
            tag = []
            for t in tags:
                text = t.text
                if not is_contain_chinese(text):
                    text = text.lower()
                if text not in tag:
                    tag.append(text)
                    if len(tag) == 3:       #tag大于3个的只取前三个
                        tag = ('\t'.join(tag))
                        break
            if isinstance(tag,list):         #部分数目tag少于3个 全部遍历后list为转为str
                tag = ('\t'.join(tag))
            
            try:
                recdiv = h.find_all('div',attrs = {"class":"content clearfix"})[-1]
                recs = recdiv.find_all('a')
                recno = []
                for rec in recs:
                    rno = rec.attrs['href'].split('/')[-2]
                    if rno not in recno:
                        recno.append(rno)
                    recnos = (' ').join(recno)
            except:
                recnos = ''

            cover = req(cover).content
            cover = base64.b64encode(cover).decode('utf-8')
            
            c = conn.cursor()
            sql = "select * from books"
            id = len(c.execute(sql).fetchall()) +1
            no = isbn[-7:]

            sql = "INSERT INTO books ('id','title','intro','isbn','cover','itemno','tags','subno','recnos','infos','buy') \
                VALUES ('%d','%s', '%s', '%s', '%s', '%s','%s','%s','%s','%s','%s' );" %(id,title.replace('\'','’'),intro.replace('\'','’'),isbn,cover,no,tag.replace('\'','’'),subno,recnos,allinfo,buy)
            try:
                c.execute(sql)
            except IntegrityError as e:
                if e == 'UNIQUE constraint failed: books.itemno':
                    itemno = str(int(itemno) + 1)
                    c.execute(sql)
            conn.commit()
            print(title + '   成功')
            
            
    conn.close()

def is_contain_chinese(check_str):
    """
    判断字符串中是否包含中文
    :param check_str: {str} 需要检测的字符串
    :return: {bool} 包含返回True， 不包含返回False
    """
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def getproxy():
    proxy = readip.readip()
    if proxy == 'Failed to get proxies':
        return getproxy()
    return proxy

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
                