# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from concurrent import futures
from tqdm import tqdm

#隱藏warning
pd.set_option('mode.chained_assignment',None)


#定義進入每篇標的文章爬取分析資訊函數
def details_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')
    #處理可能抓不到時間的問題
    try:
        tim=s.select('div.article-metaline')[2].text[2:]
    except:
        tim=np.nan
    
    content=s.select('#main-content')[0].text.replace(' :','：').replace(':','：').replace('---','').replace('多/空/請益/心得','').replace('(非長期投資者，必須有停損機制)','')
    
    #處理可能文章格式錯誤問題
    if '1. 標的：' in content:                  
        idx_1=content.index('1. 標的：')
        idx_2=content.index('2. 分類：')
        idx_3=content.index('3. 分析/正文：')
        idx_5=content.index('--')
        
        stock=content[idx_1:idx_2].replace('\n','').split('標的：')[1].replace(' ','')
        direction=content[idx_2:idx_3].replace('\n','').split('分類：')[1].replace(':','').replace(' ','')
        
        #處理可能文章最後項目不存在格式錯誤問題
        if '4. 進退場機制：' in content:
            idx_4=content.index('4. 進退場機制：')
            analysis=content[idx_3:idx_4].replace('\n','').split('正文：')[1].replace(' ','')
            stop=content[idx_4:idx_5].replace('\n','').split('進退場機制：')[1].replace(' ','')
        else:
            #若文章格式不對將剩下所有內容指派到分析欄位
            analysis=content[idx_3:idx_5].replace('\n','').split('正文：')[1].replace(' ','')
            stop=np.nan
             
    else:
        idx_1=content.index('\n\n')
        idx_2=content.index('--')
        
        stock=np.nan
        direction=np.nan
        #若文章格式不對將所有內容指派到分析欄位
        analysis=content[idx_1:idx_2].replace('\n','').replace(' ','')
        stop=np.nan
    
    return i,tim,stock,direction,analysis,stop


#定義爬取單頁Stock板標的文章資訊函數
def ptt_stock_crawler(url):   
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')
    entrys=soup.select('div.r-ent')
    
    titles,dates,authors,recommends,links=[],[],[],[],[]

    for entry in entrys:
        try:
            titles.append(entry.select('div.title a')[0].text)
        except:
            titles.append(np.nan)
        try:
            links.append('https://www.ptt.cc{}'.format(entry.select('div.title a')[0]['href']))
        except:
            links.append(np.nan)
        
        dates.append(entry.select('div.date')[0].text)
        if entry.select('div.author')[0].text=='-':
            authors.append(np.nan)
        else:
            authors.append(entry.select('div.author')[0].text)  
        
        if entry.select('div.nrec')[0].text=='':
            recommends.append(np.nan)
        else:
            recommends.append(entry.select('div.nrec')[0].text) 
    
    df=pd.DataFrame({
        '標題':titles,
        '日期':dates,
        '作者':authors,
        '推數':recommends,
        '網址':links
    })
    df.dropna(axis=0,inplace=True)
    df['推數'].replace('爆','99',inplace=True)
    df=df[~df['推數'].str.startswith('X')]
    df_s=df[(df['標題'].str.contains('標的'))&(~df['標題'].str.contains('Re:'))&(~df['標題'].str.contains('R:'))]
    df_s.reset_index(drop=True,inplace=True)
    
    #處理標的文特殊欄位
    link_list=[]
    for i in range(len(df_s['網址'])):
        link_list.append([df_s['網址'][i],i])
    
    times=[0]*len(df_s['網址'])
    stocks=[0]*len(df_s['網址'])
    directions=[0]*len(df_s['網址'])
    analyses=[0]*len(df_s['網址'])
    stops=[0]*len(df_s['網址'])
    
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(executor.map(details_crawler,link_list))
        
        for future in results:
            i,tim,stock,direction,analysis,stop=future
            times[i]=tim
            stocks[i]=stock
            directions[i]=direction
            analyses[i]=analysis
            stops[i]=stop
    
    df_s.loc[:,'時間']=times
    df_s.loc[:,'標的']=stocks
    df_s.loc[:,'方向']=directions
    df_s.loc[:,'分析']=analyses
    df_s.loc[:,'進退場']=stops
    
    return df,df_s


#定義爬取多頁Stock板標的文章資訊函數
def page_function(page):    
    url='https://www.ptt.cc/bbs/Stock/index.html'
    dfs,dfs_s=[],[]
    df,df_s=ptt_stock_crawler(url)
    dfs.append(df)
    dfs_s.append(df_s)
    
    for i in tqdm(range(page)):
        response=requests.get(url)
        soup=BeautifulSoup(response.text,'html.parser')
        paging=soup.select('div.btn-group-paging a')
        url='https://www.ptt.cc{}'.format(paging[1]['href'])
        df,df_s=ptt_stock_crawler(url)
        dfs.append(df)
        dfs_s.append(df_s)
    
    df=pd.concat(dfs,ignore_index=True)
    df_s=pd.concat(dfs_s,ignore_index=True) 
    
    return df,df_s  


#抓取Stock板標的文章資訊
df,df_s=page_function(20)
#將Stock板標的文章資訊匯出成Excel檔
df_s.to_excel('Stock板標的文.xlsx',index=False)






