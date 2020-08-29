# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from tqdm import tqdm


#定義爬取104人力銀行職缺資訊函數
def job_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    articles=soup.select('article.b-block--top-bord.job-list-item.b-clearfix.js-job-item')
    titles=[e.select('a')[0].text for e in articles]
    companys=[e.select('a')[1].text.replace('\n','').replace(' ','') for e in articles]
    links=['https:{}'.format(e.select('a')[1]['href']) for e in articles]
    statuses=[e.select('a')[2].text.split('應徵')[0] for e in articles]
    dates=[e.select('span')[0].text.replace('\n','').replace(' ','') for e in articles]
    salaries=[e.select('span')[1].text for e in articles]
    locations=[e.select('ul.b-list-inline.b-clearfix.job-list-intro.b-content>li')[0].text for e in articles]
    requirements=[e.select('ul.b-list-inline.b-clearfix.job-list-intro.b-content>li')[1].text for e in articles]
    degrees=[e.select('ul.b-list-inline.b-clearfix.job-list-intro.b-content>li')[2].text for e in articles]
    texts=[e.select('p')[0].text.replace('\r','').replace('\n','').replace('\t','') for e in articles]
    
    dates,industrys=[],[]
    for e in articles:
        if e.select('span')[0].text.replace('\n','').replace(' ','')=='':
            dates.append(np.nan)
        else:
            dates.append(e.select('span')[0].text.replace('\n','').replace(' ',''))
    
    for e in articles:
        if len(e.select_one('ul.b-list-inline.b-clearfix').select('li'))==3:
            industrys.append(e.select_one('ul.b-list-inline.b-clearfix').select('li')[-1].text)
        else:
            industrys.append(np.nan)
    
    df=pd.DataFrame({
        '日期':dates,
        '應徵':statuses,
        '工作':titles,
        '公司':companys,
        '產業':industrys,
        '薪水':salaries,
        '地區':locations,
        '要求':requirements,
        '學歷':degrees,
        '介紹':texts,
        '網址':links
    })
    
    return df


#定義爬取多頁104人力銀行關鍵字職缺資訊函數
def page_function(keyword,page):
    dfs=[]
    
    for i in tqdm(range(page)):
        url='https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword={}&order=1&asc=0&page={}&mode=s'.format(keyword,i+1)
        d=job_crawler(url)
        dfs.append(d)
    
    df=pd.concat(dfs,ignore_index=True)
    
    return df


#抓取指定總頁數104人力銀行關鍵字職缺資訊
df=page_function('金融實習',3)
#將104人力銀行關鍵字職缺資訊匯出成Excel檔
df.to_excel('104金融實習.xlsx',index=False)




