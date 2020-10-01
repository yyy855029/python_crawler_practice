# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from urllib.request import urlretrieve


#定義爬取永慶房仲網房屋資訊函數
def yungching_house_crawler(url):
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    #添加User-Agent
    response=requests.get(url,headers)
    soup=BeautifulSoup(response.text,'html.parser')
    
    houses=soup.select('li.m-list-item.vr')
    titles=[e.select('a')[1].text.split('\u3000')[0] for e in houses]
    locations=[e.select('a')[1].text.split('\u3000')[1] for e in houses]
    links=['https://buy.yungching.com.tw'+e.select('a')[0]['href'] for e in houses]
    types=[e.select('li')[0].text for e in houses]
    years=[e.select('li')[1].text.replace('\n','').replace('\r','') for e in houses]
    floors=[e.select('li')[2].text.replace('\n','').replace('\r','') for e in houses]
    lands=[e.select('li')[3].text.strip('土地 ') for e in houses]
    livings=[e.select('li')[4].text for e in houses]
    buildings=[e.select('li')[5].text.strip('建物 ') for e in houses]
    rooms=[e.select('li')[6].text.replace('\n','').replace('\r','') for e in houses]
    prices=[e.select('div.price')[0].text for e in houses]
    imgs=['https:'+e.select('img')[0]['src'] for e in houses]
    
    df=pd.DataFrame({
        '標題':titles,
        '地點':locations,
        '類型':types,
        '年數':years,
        '樓層':floors,
        '土地':lands,
        '主廳':livings,
        '建物':buildings,
        '房間數':rooms,
        '價格':prices,
        '網址':links,
        '照片':imgs
    })        
    
    return df


#定義爬取多頁永慶房仲網房屋資訊函數
def page_function(page):
    info=pd.DataFrame()
    urls=['https://buy.yungching.com.tw/region?pg={}'.format(i+1) for i in range(page)]
    
    dfs=[]
    for url in urls:
        d=yungching_house_crawler(url)
        dfs.append(d)
    df=pd.concat(dfs,ignore_index=True)
    
    return df


#抓取指定總頁數永慶房仲網房屋資訊
df=page_function(5)
#將永慶房仲網房屋資訊匯出成Excel檔
df.to_excel('永慶房仲網房屋資訊.xlsx',index=False)


#抓取永慶房仲網房屋資訊封面照
titles=df['標題'].values.tolist()
imgs=df['照片'].values.tolist()

directory='永慶房仲網房屋照片'
if not os.path.isdir(directory):
    os.makedirs(directory)

#執行方便,以前10筆資料為例
for title,img in zip(titles[:10],imgs[:10]):    
    print(title)
    urlretrieve(img,directory+'/{}.jpg'.format(title))
