# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import json
import numpy as np
import pandas as pd
import time
from datetime import datetime,timezone,timedelta
from tqdm import tqdm
from concurrent import futures


#定義爬取每篇鉅亨網台股新聞內容函數
def article_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')
    article=''.join([e.text.replace('\n','') for e in s.select('._2E8y>p')])
    time.sleep(0.5)

    return i,article


#定義爬取單頁鉅亨網台股新聞資訊函數
def cnyes_news_crawler(url_list):
    url=url_list[0]
    j=url_list[1]
    response=requests.get(url)
    #json格式
    dicts=json.loads(response.text)
    data=dicts['items']['data']

    #網站時間是UTC+0(格林威治標準時間)，要調整成台灣時區UTC+8(東八區)
    publish_Ats=[np.datetime64(datetime.utcfromtimestamp(data[i]['publishAt']).replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')) for i in range(len(data))]
    news_Ids=[data[i]['newsId'] for i in range(len(data))]
    links=['https://news.cnyes.com/news/id/{}?exp=a'.format(id_num) for id_num in news_Ids]
    titles=[data[i]['title'] for i in range(len(data))]
    summaries=[data[i]['summary'] for i in range(len(data))]
    markets=[data[i]['market'] for i in range(len(data))]

    articles=[0]*len(links)
    link_list=[[links[i],i] for i in range(len(links))]
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(executor.map(article_crawler,link_list))
        for future in results:
            i,article=future
            articles[i]=''.join(article)

    df=pd.DataFrame({
        '時間':publish_Ats,
        '編號':news_Ids,
        '標題':titles,
        '簡介':summaries,
        '內容':articles,
        '影響個股':markets,
        '連結':links
    })
        
    return j,df


#定義爬取指定時間範圍下每頁鉅亨網台股新聞資訊函數
def time_range_page_crawler(starttime,endtime):
    #starttime和endtime間距不能超過60天
    startAt=int(time.mktime(starttime.timetuple()))
    endAt=int(time.mktime(endtime.timetuple()))
    start_url='https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?startAt={}&endAt={}&isCategoryHeadline=1&limit=30'.format(startAt,endAt)
    
    response=requests.get(start_url)
    #json格式
    dicts=json.loads(response.text)
    total_page=dicts['items']['last_page']
    url_links=[start_url+'&page={}'.format(i+1) for i in range(total_page)]
    url_list=[[url_links[i],i] for i in range(len(url_links))]
    df_list=[0]*len(url_links)
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(tqdm(executor.map(cnyes_news_crawler,url_list),total=len(url_list)))
        for future in results:
            j,df=future
            df_list[j]=df
    
    merge_df=pd.concat(df_list,ignore_index=True)
    merge_df.sort_values(['時間'],inplace=True)
    merge_df.reset_index(drop=True,inplace=True)
        
    return merge_df


#定義遞迴爬取指定時間範圍下全部鉅亨網台股新聞資訊函數
def date_range_total_crawler(total_time):
    #從今天日期當起始天，往後間隔60天
    endtime=datetime.now().date()
    starttime=(endtime-timedelta(days=60))

    merge_df_list=[]
    
    #跑幾組間隔60天差距天數新聞
    for iter_time in range(total_time):
        merge_df=time_range_page_crawler(starttime,endtime)
        merge_df_list.append(merge_df)
        endtime=starttime-timedelta(days=1)
        starttime=endtime-timedelta(days=60)

    total_merge_df=pd.concat(merge_df_list,ignore_index=True)
    total_merge_df.sort_values(['時間'],inplace=True)
    total_merge_df.reset_index(drop=True,inplace=True)
    
    return total_merge_df


#遞迴爬取指定時間範圍下全部鉅亨網台股新聞資訊
total_merge_df=date_range_total_crawler(3)
#將鉅亨網台股新聞資訊匯出成Excel檔
total_merge_df.to_excel('鉅亨網台股新聞資訊.xlsx',index=False)




