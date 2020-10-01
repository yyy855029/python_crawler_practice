# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from concurrent import futures
from tqdm import tqdm


#定義爬取個別YouTube發燒影片頻道訂閱數函數
def channel_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')
    #解決從發燒影片頻道可能無訂閱數問題
    if s.select('span.yt-subscription-button-subscriber-count-branded-horizontal')==[]:
        subscription=np.nan
    else:
        subscription=s.select('span.yt-subscription-button-subscriber-count-branded-horizontal')[0].text
   
    return i,subscription


#定義爬取YouTube發燒影片資訊函數
def youtube_trending_crawler():
    url='https://www.youtube.com/feed/trending'
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    items=soup.select('div.yt-lockup-content')
    videos=[e.select('a')[0].text for e in items]
    vlinks=['https://www.youtube.com{}'.format(e.select('a')[0]['href']) for e in items]
    channels=[e.select('a')[1].text for e in items]
    clinks=['https://www.youtube.com{}'.format(e.select('a')[1]['href']) for e in items]
    days=[e.select('li')[0].text for e in items]
    times=[int(e.select('li')[1].text[5:-1].replace(',','')) for e in items]
    #解決有可能發燒影片沒影片描述問題
    descriptions=[]
    for e in items:
        if e.select('div.yt-lockup-description')==[]:
            descriptions.append(np.nan)
        else:
            descriptions.append(e.select('div.yt-lockup-description')[0].text)
    
    ranks=list(range(1,len(videos)+1))
    subscriptions=[0]*len(clinks)
    
    link_list=[]
    for i in range(len(clinks)):
        link_list.append([clinks[i],i])
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(tqdm(executor.map(channel_crawler,link_list),total=len(link_list)))

        for future in results:
            i,subscription=future
            subscriptions[i]=subscription
            
    df=pd.DataFrame({
        '排名':ranks,
        '影片':videos,
        '觀看次數':times,
        '時間':days,
        '影片連結':vlinks,
        '描述':descriptions,
        '頻道':channels,
        '訂閱數':subscriptions,
        '頻道連結':clinks
    })
    
    return df


#抓取YouTube發燒影片資訊
df=youtube_trending_crawler()
#將YouTube發燒影片資訊匯出成Excel檔
df.to_excel('YouTube發燒影片排名.xlsx',index=False)



