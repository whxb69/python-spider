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
import urllib

ua = UserAgent()
conn = sqlite3.connect(r'jdbook.db')


def main():
    url = 'https://channel.jd.com/1713-3287.html'
    html = req(url, 'utf-8').text
    soup = BeautifulSoup(html)
    menu = soup.find('div', attrs={"class": 'menu'})
    cates = menu.find_all('div', attrs={"class": 'ui-switchable-menu'})
    #一级标签
    for cate in cates:
        p = subcates = cate.find('p')
        if p:
            #二级标签
            subcates = p.find_all('a')
            for subcate in subcates:
                # title = subcate.attrs['title']
                link = subcate.attrs['href']
                # print('%s\t开始'% title)
                spider(link)


'''
flink:当前cate的第一页链接
'''

def spider(flink):
    flink = 'https:' + flink
    host = flink.split('/')[2]
    pvid = re.findall('&pvid=.+#', flink)
    if pvid:
        flink = flink.replace(pvid[0], '')
    html, ua_ = req(flink, ['utf-8'], return_ua=True)
    soup = BeautifulSoup(html)
    allul = soup.find('ul', attrs={'class': 'gl-warp'})

    #本页前30个item
    lis = allul.find_all('li', attrs={'class': 'gl-item'})
    #本页后30个item
    #TODO:分析请求
    try:
        page = re.findall('page=\d+', flink)[0][5:]
    except:
        page = 1
    
    url = 'https://search.jd.com/s_new.php?keyword=Python&enc=utf-8&qrst=1&rt=1&stop=1&book=y&vt=2&stock=1&page=%d&s=%d&scrolling=y&log_id=%.5f&tpl=2_M' % (
        page + 1, 30 * page + 1, time.time())
    #解析url参数
    q_dict = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(flink).query))
    
    headers_ = {
            'authority': host,
            'method': 'GET',
            'path': re.sub('https://\w+.jd.com','',url),
            'scheme': 'https',
            'Referer': flink.replace('click=1','click=0'),
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'User-Agent': ua_,
            'x-requested-with': 'XMLHttpRequest'
                }
    
    html_ = req(url, ['utf-8'], headers_).text
    soup_ = BeautifulSoup(html_)
    lis_ = soup_.find_all('li', attrs={'class': 'gl-item'})
    lis += lis_ 
    for li in lis:
        a = li.find('div', attrs={'class': 'p-name'}).find('a', attrs={'target': '_blank'})
        # title = a.attrs['title'].strip().replace("'",'‘')
        href = a.attrs['href']
        try:
            author = li.find('span', attrs={"class": 'p-bi-name'}).find('a').attrs['title']
        except:
            author = '佚名'

        headers_i = {
                'Host': 'gia.jd.com',
                'Origin': 'https://item.jd.com',
                'Referer': 'https:' + href,
                'User-Agent': ua_
        }
        ihtml = req('https:' + href, ['gbk']).text
        isoup = BeautifulSoup(ihtml)
        paras = isoup.find('ul', attrs={'class': 'p-parameter-list'})
        title = isoup.find('div', attrs={
            "class": 'sku-name'
        }).text.strip().replace("'", '‘')
        if paras:
            paras = paras.find_all('li')
            #isbn位置不固定 需要寻找
            for para in paras:
                if 'ISBN' in para.text:     
                    isbn = str(para.text)
                    break
            isbn_re = re.findall('\d+', isbn)
            if len(isbn_re):
                isbn = isbn_re[0]
            else:
                isbn = ''
        #写入数据库
        c = conn.cursor()
        sql = "select * from jd_cs"
        nid = len(c.execute(sql).fetchall()) + 1
        sql = "INSERT INTO jd_cs ('id','title','author','isbn') \
				VALUES ('%d','%s', '%s', '%s');"       \
          % (nid, title, author.replace('\'', '’'), isbn)

        try:
            c.execute(sql)
            conn.commit()
            print(title + '   成功')
        except IntegrityError as e:
            #不记录isbn重复项目
            print(e)
            if e == 'UNIQUE constraint failed: jd_cs.isbn':
                print(title + '   已存在')
                continue
        time.sleep(2)
    #下一页链接 分search和list两类
    if 'search' in host:
        nextlink = '//%s/Search?keyword=%s&enc=utf-8&qrst=1&rt=1&stop=1&book=y&vt=2&stock=1&page=%d&s=%d&click=1' % (host, q_dict['keyword'] , page+2, 30*(page+1)+1)
    elif 'list' in host:
        nextlink = '//%s/list.html?cat=%s&page=%d&sort=sort_rank_asc&trans=1&JL=6_0_0#J_main' % (host, q_dict['cat'], page+1)
    #爬取下一页
    print('第%d页完成' % page)
    time.sleep(30)    
    spider(nextlink)


'''
encodes: 各页面编码，试验得出，防止中文乱码
'''


def req(url, encodes, headers_ = None, return_ua = False):
    # proxies = getproxy()
    headers = {'User-Agent': ua.random}
    #更新header
    if headers_:
        headers.update(headers_)
    res = requests.get(url=url, headers=headers, timeout=500)
    #解决中文乱码
    for encode in encodes:
        res.encoding = encode
    #是否返回user-agent
    if return_ua:
        return res.text,headers['User-Agent']
    else:
        return res


if __name__ == '__main__':
    main()
