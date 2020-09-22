# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from concurrent import futures
from tqdm import tqdm
from datetime import datetime
import re


#定義進入每篇文章爬取推文資訊函數
def details_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')
    
    #文章內文
    content=s.select('#main-content')[0]
    if  '-----' in content.text:
        temp_info=content.text.split('-----')[0]
    else:
        temp_info=content.text.split('--')[0]
    info='\n'.join(temp_info.split('\n')[1:])
    
    #暱稱和日期
    temp=content.select('.article-meta-value')
    
    if temp==[]:
        date=np.nan
        name=np.nan
    else:
        date=datetime.strptime(temp[3].text,'%a %b %d %H:%M:%S %Y')
        temp_name=re.findall(r'\((\w+)\)',temp[0].text)
        if temp_name==[]:
            name=np.nan
        else:
            name=temp_name[0]
        
    #推文和分數
    comment=[]
    total_score=0
    
    try:
        for e in content.select('.push'):
            push_tag=e.select('.hl.push-tag')[0].text.replace(' ','')
            push_user=e.select('.f3.hl.push-userid')[0].text
            push_content=e.select('.f3.push-content')[0].text.strip(': ')
            push_time=e.select('.push-ipdatetime')[0].text.strip('\n').strip(' ')

            if '推' in push_tag:
                score=1
            elif '噓' in push_tag:
                score=-1
            else:
                score=0

            total_score+=score

            comment.append({'帳號':push_user,
                            '內容':push_content,
                            '心情':push_tag,
                            '分數':score,
                            '時間':push_time})
    except:
        pass
        
    return i,info,name,date,comment,total_score


#定義爬取單頁Womentalk板文章資訊函數
def ptt_womentalk_crawler(url):   
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')
    
    entrys=soup.select('div.r-ent')
    
    titles,ids,recommends,links=[],[],[],[]

    for entry in entrys:
        if entry.select('div.author')[0].text=='-':
            continue
        else:
            titles.append(entry.select('div.title a')[0].text)
            links.append('https://www.ptt.cc'+entry.select('div.title a')[0]['href'])
            ids.append(entry.select('div.author')[0].text)
            recommends.append(entry.select('div.nrec')[0].text)
    
    link_list=[]
    for i in range(len(links)):
        link_list.append([links[i],i])
    
    infos=[0]*len(links)
    names=[0]*len(links)
    dates=[0]*len(links)
    comments=[0]*len(links)
    total_scores=[0]*len(links)
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(executor.map(details_crawler,link_list))

        for future in results:
            i,info,name,date,comment,total_score=future
            infos[i]=info
            names[i]=name
            dates[i]=date
            comments[i]=comment
            total_scores[i]=total_score
    
    df=pd.DataFrame({
        '標題':titles,
        '時間':dates,
        '帳號':ids,
        '暱稱':names,
        '推數':recommends,
        '分數':total_scores,
        '內容':infos,
        '推文':comments,
        '網址':links
    })
    
    return df


#定義爬取多頁Womentalk板文章資訊函數
def page_condition_function(page):    
    url='https://www.ptt.cc/bbs/WomenTalk/index.html'    
    dfs=[]
   
    for i in tqdm(range(page)):    
        d=ptt_womentalk_crawler(url)
        dfs.append(d)
        response=requests.get(url)
        soup=BeautifulSoup(response.text,'html.parser')
        paging=soup.select('div.btn-group-paging a')
        url='https://www.ptt.cc'+paging[1]['href']
    
    df=pd.concat(dfs,ignore_index=True)
    
    return df


#抓取指定總頁數Womentalk板文章資訊
df=page_condition_function(10)
#將Womentalk板文章資訊匯出成Excel檔
df.to_excel('Womentalk板文章資訊.xlsx',index=False)








