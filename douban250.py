from bs4 import BeautifulSoup
import requests
import os

for i in range(10):
    if i == 0:
        url = 'https://movie.douban.com/top250'
    else:
        url = 'https://movie.douban.com/top250?start=' + str(25*i) + '&filter='
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'}
    url_get = requests.get(url,headers = header)
    url_decode = url_get.content #gb2312为网页编码
    url_soup = BeautifulSoup(url_decode,'html.parser')
    all_a = url_soup.find('div',id = 'content').find_all('a',attrs={"class":""}) #此处attrs={"class":"title"}必须为大括号
    # print(a)
    for a in all_a:
        b = BeautifulSoup(str(a),'html.parser')
        # print(b)
        if b.img:
            title = b.img['alt'] #取得<a>标签中的text
            jpg = b.img['src']
            print(title)
            print(jpg)
            jpg = requests.get(jpg, headers=header)  # jpg文件地址解析
            f = open("E:\\top250\\" + title + '.jpg', 'ab')
            f.write(jpg.content)
            print(title + ' saved')
            f.close()

print('all finished!')
