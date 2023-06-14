# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent import futures
from tqdm import tqdm
import os
from urllib.request import urlretrieve


#定義爬取個別IMDb電影資訊細節函數
def details_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')
   
    details=s.select('div.heroic-overview')[0]
    
    return i,details


#定義爬取IMDb排名電影資訊函數
def imdb_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    dramas=soup.select('tbody>tr')
    ranks=[e.select('td.titleColumn')[0].text.replace('\n','').replace('  ','').split('.')[0] for e in dramas]
    titles=[e.select('td.titleColumn')[0].select('a')[0].text.replace(':','-') for e in dramas]
    years=[e.select('td.titleColumn')[0].select('span')[0].text for e in dramas]
    links=['https://www.imdb.com{}'.format(e.select('td.titleColumn')[0].select('a')[0]['href']) for e in dramas]
    points=[float(e.select('td.ratingColumn.imdbRating')[0].text.replace('\n','')) for e in dramas]

    summarys=[0]*len(links)
    directors=[0]*len(links)
    writers=[0]*len(links)
    stars=[0]*len(links)
    lengths=[0]*len(links)
    types=[0]*len(links)
    releases=[0]*len(links)
    imgs=[0]*len(links)
   
    link_list=[]
    for i in range(len(links)):
        link_list.append([links[i],i])


    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(tqdm(executor.map(details_crawler,link_list),total=len(link_list)))

        for future in results:
            i,details=future
            directors[i]=details.select('div.credit_summary_item')[0].text.replace('\n','').replace('  ','').split(':')[1].split('|')[0]
            writers[i]=details.select('div.credit_summary_item')[1].text.replace('\n','').replace('  ','').split(':')[1].split('|')[0]
            stars[i]=details.select('div.credit_summary_item')[2].text.replace('\n','').split(':')[1].split('|')[0]
            summarys[i]=details.select('div.summary_text')[0].text.replace('\n','').replace('  ','')
            types[i]=details.select('div.subtext>a')[0].text
            releases[i]=details.select('div.subtext>a')[-1].text.replace('\n','')
            lengths[i]=details.select('time')[0].text.replace('\n','').replace('  ','')
            imgs[i]=details.select('img')[0]['src']

    df=pd.DataFrame({
        '排名':ranks,
        '片名':titles,
        '發行年份':years,
        '片長':lengths,
        '類型':types,
        '分數':points,
        '演員':stars,
        '導演':directors,
        '編劇':writers,
        '首映':releases,
        '簡介':summarys,
        '網址':links,
        '照片':imgs
    })

    df['發行年份']=df['發行年份'].str.extract('\((\d+)\)')
    
    return df



#呼叫函數
if __name__ == '__main__':
    #抓取IMDb排名電影資訊
    df=imdb_crawler('https://www.imdb.com/chart/top?ref_=nv_mv_250')
    #將IMDb排名電影資訊匯出成Excel檔
    df.to_excel('IMDb電影排名.xlsx',index=False)

    #抓取IMDb電影排名照片
    titles=df['片名'].values.tolist()
    imgs=df['照片'].values.tolist()

    directory='IMDb電影劇照'
    if not os.path.isdir(directory):
        os.makedirs(directory)

    #執行方便,以前10名照片為例
    for title,img in zip(titles[:10],imgs[:10]):    
        print(title)
        urlretrieve(img,directory+'/{}.jpg'.format(title))


    
    
