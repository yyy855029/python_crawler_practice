# coding: utf-8

#載入所需套件
import requests
import pandas as pd
import os
import time


#定義爬取個股財報資料函數
def financial_statement(stock_id,year,season,statement='綜合損益彙總表'):   
    #若輸入西元年調整成民國年
    if year>=1911:
        year-=1911
   
    form_data={'encodeURIComponent':1,
               'step':1,
               'firstin':1,
               'off':1,
               'co_id':stock_id,
               'year':year,
               'season':season}
    
    if statement=='資產負債彙總表':
        url='https://mops.twse.com.tw/mops/web/ajax_t164sb03'
        #餵入form_data
        response=requests.post(url,form_data)
        df=pd.read_html(response.text)[1].fillna('')
        df=df.iloc[:,:-2]
    elif statement=='綜合損益彙總表':
        url='https://mops.twse.com.tw/mops/web/ajax_t164sb04'
        #餵入form_data
        response=requests.post(url,form_data)
        df=pd.read_html(response.text)[1].fillna('')
        df=df.iloc[:,:-1]
    elif statement=='現金流量彙總表':
        url='https://mops.twse.com.tw/mops/web/ajax_t164sb05'
        #餵入form_data
        response=requests.post(url,form_data)
        df=pd.read_html(response.text)[1].fillna('')
        df=df.iloc[:,:-4]
    else:
        print('此類型不存在')
    
    return df


#爬取指定時間範圍個股各項財報資料
stock_ids=[2303,2330]
years=range(106,108)
seasons=range(1,5)
statements=['資產負債彙總表','綜合損益彙總表','現金流量彙總表']

for stock_id in stock_ids:
    print('{}:'.format(stock_id))
    for year in years:
        print('{}年'.format(year))
        for season in seasons:
            print('第{}季'.format(season))
            directory='每季個股財務報表資料/{}/{}年/第{}季'.format(stock_id,year,season)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            for statement in statements:            
                if not os.path.exists(directory+'/{}.xlsx'.format(statement)):
                    df=financial_statement(stock_id,year,season,statement)
                    df.to_excel(directory+'/{}.xlsx'.format(statement))
                    time.sleep(3)    

                    
                    
