import ic_spider
import sys
import pandas as pd
import os
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sqlite3

conn = sqlite3.connect(r'data.db')


def main():
    basedir = 'E:\\digidata'
    flist = [file for file in os.listdir(basedir) if os.path.splitext(file)[1] == '.csv']
    #遍历文件
    for file in flist:
        #编号去重
        content = pd.read_csv(open(basedir+ '\\' + file, 'r', encoding='utf-8'))
        _content = content.drop_duplicates('制造商零件编号')
        #遍历各零件
        for row in _content.iterrows():
            cookie = {}
            key_word = str(row[1].制造商零件编号)
            url = "https://www.ic.net.cn/search.php?IC_Method=icsearch&key=%s&isExact=0&mfg=&pack=&dc=&qty=&searchAreaCode=0&stockDate=90&stockType=0" % key_word
            #selenium获取cookie
            chrome_options = Options()
            # chrome_options.add_argument('--headless')
            # chrome_options.add_argument('--disable-gpu')
            broswer = webdriver.Chrome(chrome_options=chrome_options)

            broswer.get('https://www.ic.net.cn/')
            broswer.find_element_by_xpath('//*[@id="key"]').send_keys(key_word)
            broswer.find_element_by_xpath('//*[@id="btn_topSearch"]').click()

            cookie_str = ''
            for x in broswer.get_cookies():
                cookie_str += '%s=%s;' % (x['name'], x['value'])
            page = ic_spider.main(url, cookie_str, key_word)
            broswer.close()
            if page!=0:
                date = time.strftime("%Y-%m-%d", time.localtime())
                sql = "INSERT INTO urls('lastdate','url','cookie','pages','key_word') VALUES ('%s','%s','%s','%s','%s')"%(date,url,cookie_str,str(page),key_word)
                c = conn.cursor()
                c.execute(sql)
                conn.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()
