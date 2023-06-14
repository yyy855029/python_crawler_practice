# coding: utf-8

#載入所需套件
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from concurrent import futures
from tqdm import tqdm
import os
from urllib.request import urlretrieve


#定義爬取個別Yahoo電影院線片資訊細節函數
def details_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link,stream=True)
    s=BeautifulSoup(r.text,'html.parser')
    movie_intro_info_r=s.select('div.movie_intro_info_r')[0]
    
    return i,movie_intro_info_r    


#定義爬取Yahoo電影院線片資訊函數
def yahoo_movie_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    movies=soup.select('ul.release_list>li')
    cnames=[e.select('a')[1].text.replace('\n','').replace(' ','') for e in movies]
    links=[e.select('a')[1]['href'] for e in movies] 
    popularitys=[e.select('div.leveltext>span')[0].text for e in movies]
    points=[e.select('span.count')[0]['data-num'] for e in movies]
    texts=[e.select('div.release_text')[0].text.replace('\n','').replace('\r','').replace(' ','') for e in movies]
    dates=[e.select('div.release_movie_time')[0].text.split(' ： ')[1] for e in movies]
    imgs=[e.select('img')[0]['src'] for e in movies]
    #處理可能英文電影名遺漏值
    enames=[]
    for e in movies:
        if e.select('a')[2].text.replace('\n','').replace('  ','')=='':
            enames.append(np.nan)
        else:
            enames.append(e.select('a')[2].text.replace('\n','').replace('  ',''))
            
    directors=[0]*len(links)
    actors=[0]*len(links)
    periods=[0]*len(links)
    companys=[0]*len(links)
    imdbs=[0]*len(links)
            
    link_list=[]
    for i in range(len(links)):
        link_list.append([links[i],i])       
    
     #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(executor.map(details_crawler,link_list))

        for future in results:
            i,movie_intro_info_r=future
            directors[i]=movie_intro_info_r.select('div.movie_intro_list')[0].text.replace('\n','').replace(' ','')
            periods[i]=movie_intro_info_r.select('span')[1].text.split('：')[1]
            companys[i]=movie_intro_info_r.select('span')[2].text.split('：')[1]
            #處理可能演員遺漏值
            if movie_intro_info_r.select('div.movie_intro_list')[1].text.replace('\n','').replace(' ','')=='':
                actors[i]=np.nan
            else:
                actors[i]=movie_intro_info_r.select('div.movie_intro_list')[1].text.replace('\n','').replace(' ','')
            #處理可能IMDb分數遺漏值
            if movie_intro_info_r.select('span')[3].text.split('：')[1]=='':
                imdbs[i]=np.nan
            else:
                imdbs[i]=movie_intro_info_r.select('span')[3].text.split('：')[1]
    
    df=pd.DataFrame({
        '中文電影名':cnames,
        '英文電影名':enames,
        '上映日':dates,
        '導演':directors,
        '演員':actors,
        '片長':periods,
        'IMDb分數':imdbs,
        '期待度':popularitys,
        '滿意度':points,
        '介紹':texts,
        '網址':links,
        '電影劇照':imgs
    })        
    
    return df


#定義爬取多頁Yahoo電影院線片資訊函數
def page_function(page):
    dfs=[]
    
    for i in tqdm(range(page)):
        url='https://movies.yahoo.com.tw/movie_intheaters.html?page={}'.format(i+1)
        d=yahoo_movie_crawler(url)
        dfs.append(d)
    
    df=pd.concat(dfs,ignore_index=True)
    
    return df



#呼叫函數
if __name__ == '__main__':
    #抓取指定總頁數Yahoo電影院線片資訊
    df=page_function(5)
    #將Yahoo電影院線片資訊匯出成Excel檔
    df.to_excel('Yahoo電影院線片資訊.xlsx',index=False)

    #抓取Yahoo電影院線片劇照
    cnames=df['中文電影名'].values.tolist()
    imgs=df['電影劇照'].values.tolist()

    directory='Yahoo電影院線片劇照'
    if not os.path.isdir(directory):
        os.makedirs(directory)

    #執行方便,以前10筆資料為例
    for cname,img in zip(cnames[:10],imgs[:10]):    
        print(cname)
        urlretrieve(img,directory+'/{}.jpg'.format(cname))














