# coding: utf-8

#載入所需套件
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


#定義抓取指定時間和恒指區域牛熊證街貨分佈資料
def bear_bull_crawler(date,code):
    url='https://www.bocifp.com/tc/cbbc/cbbc-hsi-os?date={}&spread={}'.format(date,code)
    response=requests.get(url)
    dfs=pd.read_html(response.text)
    
    soup=BeautifulSoup(response.text,'html.parser')
    #對沖張數(一日變化)提取()內一日變化數值
    bear_diff=[re.findall(r'.*\((.*)\).*',e.text)[0]  for index,e in enumerate(soup.select('.data')) if index<=13]
    bull_diff=[re.findall(r'.*\((.*)\).*',e.text)[0]  for index,e in enumerate(soup.select('.data')) if index>13]
    
    #中銀精選和收回價
    price_bear=dfs[3].iloc[:14,:]
    price_bull=dfs[3].iloc[15:,:]
    price_bull.reset_index(drop=True,inplace=True)
    
    #牛熊證比例
    bull_bear_perct=dfs[0]
    bull_bear_perct.columns=['標題','類別']
    bull_bear_perct['熊證比例']=bull_bear_perct['類別'].apply(lambda x:x.split('  ')[0])
    bull_bear_perct['牛證比例']=bull_bear_perct['類別'].apply(lambda x:x.split('  ')[1])
    bull_bear_perct=bull_bear_perct[['熊證比例','牛證比例']]
    
    df_bear=dfs[1].iloc[:15,:2]
    headers=df_bear.iloc[0]
    df_bear=pd.DataFrame(df_bear.values[1:],columns=headers)
    df_bear['收回價']=df_bear['熊證'].apply(lambda x:x.split('  ')[0].split(':')[1])
    df_bear['街貨量(百萬份)']=df_bear['熊證'].apply(lambda x:x.split('  ')[1].split(':')[1])
    df_bear['街貨相對期指張數(張)']=df_bear['熊證'].apply(lambda x:x.split('  ')[2].split(':')[1])
    df_bear.columns=['指數','熊證','收回價','街貨量(百萬份)','街貨相對期指張數(張)']
    df_bear['街貨相對期指張數一日變化(張)']=bear_diff
    df_bear=df_bear[['指數','收回價','街貨量(百萬份)','街貨相對期指張數(張)','街貨相對期指張數一日變化(張)']]
    
    
    df_bull=dfs[1].iloc[16:,:2]
    df_bull.columns=['指數','牛證']
    df_bull.reset_index(drop=True,inplace=True)
    df_bull.drop(df_bull.index[-1],inplace=True)
    df_bull['收回價']=df_bull['牛證'].apply(lambda x:x.split('  ')[0].split(':')[1])
    df_bull['街貨量(百萬份)']=df_bull['牛證'].apply(lambda x:x.split('  ')[1].split(':')[1])
    df_bull['街貨相對期指張數(張)']=df_bull['牛證'].apply(lambda x:x.split('  ')[2].split(':')[1])
    df_bull['街貨相對期指張數一日變化(張)']=bull_diff
    df_bull=df_bull[['指數','收回價','街貨量(百萬份)','街貨相對期指張數(張)','街貨相對期指張數一日變化(張)']]
    
    total_bear_df=pd.concat([df_bear,price_bear],axis=1)
    total_bull_df=pd.concat([df_bull,price_bull],axis=1)
    total_bear_bull_df=pd.concat([total_bear_df,total_bull_df],axis=0,ignore_index=True)
    
    return bull_bear_perct,total_bear_df,total_bull_df,total_bear_bull_df



#呼叫函數
if __name__ == '__main__':
    #指定恒指區域抓取當天牛熊證街貨分佈資料
    date=datetime.now().strftime('%Y-%m-%d')

    diff_dict={'50':'0',
              '100':'1',
              '200':'2',
              '300':'3',
              '400':'4',
              '500':'5'}

    condition=True
    while condition:
        try:
            diff=str(input('輸入恒指區域 (50, 100, 200, 300, 400, 500) : '))
            code=diff_dict[diff]
            condition=False
        except:
            print('請輸入正常範圍 !!')

    bull_bear_perct,total_bear_df,total_bull_df,total_bear_bull_df=bear_bull_crawler(date,code)

    #將指定恒指區域當天牛熊證街貨分佈資料匯出成Excel檔
    total_bear_bull_df.to_excel('{}恒指區域{}牛熊證街貨分佈圖.xlsx'.format(date,diff),index=False)




