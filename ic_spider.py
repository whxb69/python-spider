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

try:
    ua = UserAgent()
except:
    ua = UserAgent()
conn = sqlite3.connect(r'data.db')


def main(url,cookie, pages, key, refresh=False):
    baseurl = url
    cookie = cookie
    html = req(url, cookie).text
    soup = BeautifulSoup(html)
    # pages = len(soup.find('div',attrs={'class':"pagepicker"}).find_all('li'))
    print('共%d页数据 正在爬取。。。'%pages)

    for i in range(1, pages+1):
        if i == 1:
            url = baseurl
        else:
            url = baseurl + '&page=' + str(i)
        if i != 1:
            html = req(url, cookie).text
            soup = BeautifulSoup(html)
        rlist = soup.find('ul', attrs={'id': "resultList"})
        lis = rlist.find_all('li', attrs={'class': "stair_tr"})
        res = {}
        for index, li in enumerate(lis[1:]):
            cates = ['supply', 'id', 'factory', 'batchNumber',
                     'totalNumber', 'pakaging', 'prompt', 'date', 'askPrice']
            res[str(index)] = {}
            for cate in cates:  # 行内遍历各列
                if cate != 'askPrice':  # 普通列
                    div = li.find('div', attrs={'class': "result_" + cate})
                    if div.text:
                        try:
                            res[str(index)][cate] = div.find('a').text.strip()
                        except:
                            if div.find('span'):
                                res[str(index)][cate] = div.find(
                                    'span').text.strip()
                            else:
                                res[str(index)][cate] = div.text.strip()
                    else:
                        res[str(index)][cate] = ''
                    if cate == 'supply':  # 获取悬浮名片内容
                        card = div.find('div', attrs={'class': "detailLayer"})
                        if card:
                            res[str(index)]['card'] = {}
                            divs = card.find(
                                'div', attrs={'class': "layer_mainContent"}).contents
                            cinfos = [div.text.strip()
                                      for div in divs if div != '\n'][:-1]
                            for cinfo in cinfos:
                                c_cate = cinfo.split('：')[0]
                                info_data = cinfo[len(
                                    c_cate) + 1:].strip().replace('\n', '\t')
                                info_data = re.sub('(\xa0)+', '\t', info_data)
                                res[str(index)]['card'][c_cate] = info_data

                else:  # 获取联系方式 qq号
                    qqs = li.find(
                        'div', attrs={'class': "result_" + cate}).find_all('a')
                    r = ''
                    for qq in qqs:
                        r += qq.attrs['title'] + ' '
                    res[str(index)][cate] = r
        # print(1)
        if refresh:
            refreshdb(res,key)
        else:
            setdb(res,key)



def setdb(rdict,key):
    for item in rdict:
        c = conn.cursor()
        sql = "select * from icnet"
        nid = len(c.execute(sql).fetchall()) + 1
        sql = "INSERT INTO icnet('id', '供货商', '型号', '厂家', '企业档案',\
                                 '手机', '询价QQ', '地址', '电话', '批号', '数量', '封装', '说明/库位', '日期',\
                                 '传真', '办公地点','key_word') VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s')" \
              % (nid, rdict[item]['supply'], rdict[item]['id'], rdict[item]['factory'], rdict[item]['card']['企业档案'],
                 rdict[item]['card']['手机'], rdict[item]['askPrice'], rdict[item]['card']['地址'],
                 rdict[item]['card']['电话'], rdict[item]['batchNumber'], rdict[item]['totalNumber'],
                 rdict[item]['pakaging'], rdict[item]['prompt'], rdict[item]['date'], rdict[item]['card']['传真'],
                 rdict[item]['card']['办公地点'], str(key))
        c.execute(sql)
        conn.commit()
        print(rdict[item]['supply'] + '   成功')

def refreshdb(rdict,key):
    for item in rdict:
        c = conn.cursor()
        sql = 'SELECT * FROM icnet WHERE 供货商="%s"' % rdict[item]['supply']
        res = c.execute(sql).fetchall()
        num = len(res)
        sql = 'SELECT * FROM icnet WHERE key_word="%s"' % key
        nid = len(c.execute(sql).fetchall()) + 1

        datas = (nid, rdict[item]['supply'], rdict[item]['id'], rdict[item]['factory'], rdict[item]['card']['企业档案'],
                 rdict[item]['card']['手机'], rdict[item]['askPrice'], rdict[item]['card']['地址'],
                 rdict[item]['card']['电话'], rdict[item]['batchNumber'], rdict[item]['totalNumber'],
                 rdict[item]['pakaging'], rdict[item]['prompt'], rdict[item]['date'], rdict[item]['card']['传真'],
                 rdict[item]['card']['办公地点'], str(key))
        items = ('id', '供货商', '型号', '厂家', '企业档案',\
                                 '手机', '询价QQ', '地址', '电话', '批号', '数量', '封装', '说明/库位', '日期',\
                                 '传真', '办公地点','key_word')
        if num == 0:

            sql = "INSERT INTO icnet('id', '供货商', '型号', '厂家', '企业档案',\
                                 '手机', '询价QQ', '地址', '电话', '批号', '数量', '封装', '说明/库位', '日期',\
                                 '传真', '办公地点','key_word') VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s')" \
              % datas
            c.execute(sql)
            conn.commit()
            print('新增 %s' % rdict[item]['supply'])
        elif num == 1:
            #TODO：比较不同值 UPDATE
            for index,(old,new) in enumerate(zip(datas,res[0])):
                if old != new and index!=0:
                    item = items[index]
                    sql = "UPDATE icnet SET %s = '%s' WHERE id = %s" % (item,new,nid)
                    c.execute(sql)
                    conn.commit()
                    print('更新 %s' % rdict[item]['supply'])
        else:
            pass


@retry(stop_max_attempt_number=10)
def req(url, cookie=None):
    # proxies = getproxy()
    headers = {'User-Agent': ua.random, 'cookie': cookie}

    res = requests.get(url=url, headers=headers, timeout=500)
    return res


if __name__ == '__main__':
    main()
