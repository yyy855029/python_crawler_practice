# coding: utf-8

#載入所需套件
import requests
import requests.packages.urllib3
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from tqdm import tqdm
import time

requests.packages.urllib3.disable_warnings()


#定義轉換日期格式函數
def process_date(date):
    date_list=[str(int(e)+1911) if i==0 else e for i,e in enumerate(date.split('/'))]
    return ''.join(date_list)


#定義爬取特定股票指定月份歷史重大訊息函數
def news_summary_crawler(year,month,co_id):
    #year:民國年
    month='{:02d}'.format(month)
    url='https://mops.twse.com.tw/mops/web/ajax_t05st01?encodeURIComponent=1&firstin=true&TYPEK=sii&year={}&month={}&co_id={}'.format(year,month,co_id)
    header={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
    response=requests.get(url,headers=header,verify=False)
    time.sleep(1.5)
    try:
        df=pd.read_html(response.text)[1]
        df.drop(df.columns[-1],axis=1,inplace=True)
        df['spoke_date']=df['發言日期'].apply(lambda x:process_date(x))
        df['spoke_time']=df['發言時間'].apply(lambda x:x.replace(':',''))

        seq_no_list=[]
        for e in df.groupby(['發言日期']).count().values[:,0]:
            for i in range(1,e+1):
                seq_no_list.append(str(i))

        df['seq_no']=seq_no_list
        df['link']=url+'&spoke_date='+df['spoke_date']+'&spoke_time='+df['spoke_time']+'&seq_no='+df['seq_no']+'&step=2&off=1'
    
    except:
        df=pd.DataFrame(columns=['公司代號','公司名稱','發言日期','發言時間','主旨','spoke_date','spoke_time','seq_no','link'])

    return df


#定義爬取特定歷史重大訊息函數
def news_info_crawler(total_df):
    header={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
    info_dfs=[]
    links=total_df['link'].values
    columns=['序號','發言日期','發言時間','發言人','發言人職稱','發言人電話','主旨','符合條款','事實發生日','說明']
    for link in tqdm(links):
        r=requests.get(link,headers=header,verify=False)
        soup=BeautifulSoup(r.text,'html.parser')
        datas=[(''.join(e.text.splitlines())).replace('\xa0','').replace('\u3000','').replace('\t','') for e in soup.select('.odd')]
        
        if datas==[]:
            info_df=pd.DataFrame(columns=columns)
        else:
            info_df=pd.DataFrame([datas],columns=columns)
        
        info_dfs.append(info_df)
        time.sleep(1.5)
        
    total_info_df=pd.concat(info_dfs,ignore_index=True,sort=False)
    
    return total_info_df



#呼叫函數
if __name__ == '__main__':
    #爬取特定股票指定時間範圍歷史重大訊息
    co_id=2330
    dfs=[]
    for year in tqdm(range(107,109)):
        for month in range(1,13):
            df=news_summary_crawler(year,month,co_id)
            dfs.append(df)
    total_df=pd.concat(dfs,ignore_index=True,sort=False)

    #特定股票指定時間範圍歷史重大訊息簡介匯出成Excel檔
    total_df.to_excel('{}歷史重大訊息簡介.xlsx'.format(co_id),index=False)

    #爬取特定歷史重大消息
    total_info_df=news_info_crawler(total_df)

    #特定股票指定時間範圍歷史重大訊息內容匯出成Excel檔
    total_info_df.to_excel('{}歷史重大訊息內容.xlsx'.format(co_id),index=False)








