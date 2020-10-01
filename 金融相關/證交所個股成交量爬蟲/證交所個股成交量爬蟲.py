# coding: utf-8

#載入所需套件
import requests
import pandas as pd
import json
from datetime import datetime
import os
import time


#定義爬取證交所個股交易量函數
def volume_crawler(year,month,stock_id):
    date=datetime(year,month,1).strftime('%Y%m%d')
    url='http://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={}&stockNo={}&'.format(date,stock_id)
    response=requests.get(url)
    s=json.loads(response.text)
    df=pd.DataFrame(s['data'],columns=s['fields'])

    return df


#抓取指定時間範圍個股交易量資料
stock_ids=[2303,2330]
years=range(2016,2017)
months=range(1,13)

for stock_id in stock_ids:
    print('{}:'.format(stock_id))
    for year in years:
        print('{}年'.format(year))
        directory='每月個股成交量資料/{}/{}年'.format(stock_id,year)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        for month in months:            
            if not os.path.exists(directory+'/{}月.xlsx'.format(month)):
                df=volume_crawler(year,month,stock_id)
                df.to_excel(directory+'/{}月.xlsx'.format(month),index=False)
                print('{}月'.format(month))
                time.sleep(5)    






