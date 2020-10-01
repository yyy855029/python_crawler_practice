# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re 
from urllib.request import urlretrieve
import os


#定義爬取Beauty板文章資訊函數
def ptt_beauty_crawler(url):   
    form_data={'from':'/bbs/Beauty/index.html','yes':'yes'}
    session=requests.session()
    #餵入form_data
    response=session.post('https://www.ptt.cc/ask/over18',form_data)
    response=session.get(url)
    soup=BeautifulSoup(response.text,'html.parser')
    
    entrys=soup.select('div.r-ent')
    titles,dates,authors,recommends,links=[],[],[],[],[]

    for entry in entrys:
        try:
            titles.append(entry.select('div.title a')[0].text)
        except:
            titles.append(np.nan)
        try:
            dates.append(entry.select('div.date')[0].text)
        except:
            dates.append(np.nan)
        try:
            authors.append(entry.select('div.author')[0].text)    
        except:
            authors.append(np.nan)    
        try:
            recommends.append(entry.select('div.nrec')[0].text)
        except:
            recommends.append(np.nan)
        try:
            links.append('https://www.ptt.cc'+entry.select('div.title a')[0]['href'])
        except:
            links.append(np.nan)

    df=pd.DataFrame({
        '標題':titles,
        '日期':dates,
        '作者':authors,
        '推數':recommends,
        '網址':links
    })
    
    return df


#定義爬取多頁Beauty板文章資訊和推數篩選函數
def page_condition_function(page,condition):    
    url='https://www.ptt.cc/bbs/Beauty/index.html'    
    form_data={'from':'/bbs/Beauty/index.html','yes':'yes'}
    session=requests.session()
    #餵入form_data
    response=session.post('https://www.ptt.cc/ask/over18',form_data)

    #df:沒經過資料處理和推數篩選前
    dfs=[]
   
    for i in range(page):    
        d=ptt_beauty_crawler(url)
        dfs.append(d)
        response=session.get(url)
        soup=BeautifulSoup(response.text,'html.parser')
        paging=soup.select('div.btn-group-paging a')
        url='https://www.ptt.cc'+paging[1]['href']
    
    df=pd.concat(dfs,ignore_index=True)
    
    #df_c:經過資料處理和推數篩選後
    #將有NaN的文章資料從表格移除
    df_c=df.dropna(axis=0)
    #將推數為空字串的文章資料從表格移除
    df_c=df_c[df_c['推數']!='']
    #將推數為爆的改成99
    df_c['推數'].replace('爆','99',inplace=True)
    #將推數為X的文章資料從表格移除
    df_c=df_c[~df_c['推數'].str.startswith('X')]
    #將表格篩選只留下推數>=condition的文章資料
    df_c=df_c[(pd.to_numeric(df_c['推數'],errors='coerce')>=condition)]
    #重新設定新表格索引順序
    df_c.reset_index(drop=True,inplace=True)
    
    return df,df_c   


#抓取指定總頁數和推數篩選條件下Beauty板文章資訊
df,df_c=page_condition_function(5,50)
#將Beauty板文章資訊匯出成Excel檔
df.to_excel('Beauty板文章資訊.xlsx',index=False)


#爬取Beauty版文章圖片(在50推數以上)
titles=df_c['標題'].values.tolist()
links=df_c['網址'].values.tolist()


form_data={'from':'/bbs/Beauty/index.html','yes':'yes'}
reg_imgur_file=re.compile('http[s]?://[i.]*imgur.com/\w+\.(?:jpg|png|gif)')
session=requests.session()
##餵入form_data
response=session.post('https://www.ptt.cc/ask/over18',form_data)


#執行方便,以前3篇文章為例
for link,title in zip(links[:3],titles[:3]):
    response=session.get(link)
    images=reg_imgur_file.findall(response.text)
    print(title)
    directory='Beauty版文章圖片/{}'.format(title)
    
    if not os.path.isdir(directory):
        os.makedirs(directory)
    
    for image in set(images):
        ID=re.search('http[s]?://[i.]*imgur.com/(\w+\.(?:jpg|png|gif))',image).group(1)
        print(ID)
        #連結圖片檔案路徑
        urlretrieve(image,os.path.join(directory,ID))
    
    print('\n')

















