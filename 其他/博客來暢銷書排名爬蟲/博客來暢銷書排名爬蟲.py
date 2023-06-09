# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
from urllib.request import urlretrieve


#定義爬取博客來前100名暢銷書資訊函數
def books_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    items=soup.select('li.item')
    numbers=[e.select('strong')[0].text for e in items]
    links=[e.select('a')[0]['href'] for e in items]
    titles=[e.select('a')[1].text for e in items]
    authors=[e.select('a')[2].text for e in items]
    imgs=['https:'+e.select('img')[0]['src'] for e in items]
    #調整圖片尺寸大小(500*500)
    imgs=[e.split('&w')[0]+'&w=500&h=500' for e in imgs]
    #折扣+價格
    disprices=[e.select('li')[1].text.strip('優惠價：') for e in items]
    #將折扣+價格分開
    discounts,prices=[],[]

    for e in disprices:
        if '折' in e:
            discounts.append('{}折'.format(e.split('折')[0]))
            prices.append(e.split('折')[1])
        else:
            discounts.append(np.nan)
            prices.append(e)

    df=pd.DataFrame({
        '排名':numbers,
        '書名':titles,
        '作者':authors,
        '折扣':discounts,
        '價格':prices,
        '網址':links,
        '圖片':imgs
    })
    
    return df



#呼叫函數
if __name__ == '__main__':
    #抓取博客來暢銷書排名資訊
    df=books_crawler('https://www.books.com.tw/web/sys_saletopb/books/02?attribute=30&loc=act_menu_th_46_002')
    #將博客來暢銷書排名資訊匯出成Excel檔
    df.to_excel('博客來暢銷書排名資訊.xlsx',index=False)


    #抓取博客來暢銷書排名封面照
    titles=df['書名'].values.tolist()
    imgs=df['圖片'].values.tolist()

    directory='博客來暢銷書封面'

    if not os.path.isdir(directory):
        os.makedirs(directory)

    #執行方便,以前10名封面照為例
    for title,img in zip(titles[:10],imgs[:10]):
        urlretrieve(img,directory+'/{}.jpg'.format(title))
        print(title)

