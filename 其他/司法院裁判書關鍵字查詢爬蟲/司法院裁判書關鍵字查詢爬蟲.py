# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import json
import re

#隱藏warning
requests.packages.urllib3.disable_warnings()


#定義去除unicode字串函數
def process_content(input_str):
    return ''.join([c if ord(c)<=55291 else '_' for c in input_str])


#定義轉換民國年到西元年字串函數
def process_time(input_str):
    return '/'.join([str(int(e)+1911) if i==0 else e for i,e in enumerate(input_str.split('.'))])


#定義區分法院類別字串函數
def process_court(input_str):
    court_name=input_str.split(' ')[0]
    special_courts=['公務員懲戒委員會','智慧財產法院']
    for e in special_courts:
        if e in court_name:
            return e
    if '福建' in court_name:
        return court_name[2:6]
    else:
        return court_name[-4:]

    
#定義區分地點字串函數
def process_location(input_str):
    if '福建' in input_str:
        return '金門'
    elif '地方' in input_str:
        return input_str.split(' ')[0][2:4]
    elif '高等' in input_str:
        if '分院' in input_str:
            return input_str.split(' ')[1][:2]
        elif '行政' in input_str:
            return input_str[:2]
        #臺灣高等法院(後面沒有接分院)
        else:
            return '臺北'
    #公務員懲戒委員會、智慧財產法院
    else:
        return '臺北'

    
#定義司法院裁判書關鍵字查詢函數
def law_crawler(name):
    url='https://law.judicial.gov.tw/FJUD/default.aspx'

    #先get()取出會變動的參數
    session=requests.session()
    response=session.get(url,verify=False)
    soup=BeautifulSoup(response.text,'html.parser')

    VIEWSTATE=soup.select_one('#__VIEWSTATE')['value']
    VIEWSTATEGENERATOR=soup.select_one('#__VIEWSTATEGENERATOR')['value']
    VIEWSTATEENCRYPTED=soup.select_one('#__VIEWSTATEENCRYPTED')['value']
    EVENTVALIDATION=soup.select_one('#__EVENTVALIDATION')['value']

    form_data={'__VIEWSTATE':VIEWSTATE,
               '__VIEWSTATEGENERATOR':VIEWSTATEGENERATOR,
               '__VIEWSTATEENCRYPTED':VIEWSTATEENCRYPTED,
               '__EVENTVALIDATION':EVENTVALIDATION,
               'txtKW':name,
               'judtype':'JUDBOOK',
               'whosub':'0',
               'ctl00$cp_content$btnSimpleQry':'送出查詢'}

    #再post餵入form_data
    response=session.post(url,data=form_data,verify=False)
    soup=BeautifulSoup(response.text,'html.parser')
    #爬取q_value值
    q_value=soup.select_one('#hidQID')['value']

    #調整網址q_value值進入判決整理頁面
    url='https://law.judicial.gov.tw/FJUD/qryresultlst.aspx?q={}'.format(q_value)
    response=requests.get(url,verify=False)
    soup=BeautifulSoup(response.text,'html.parser')

    #紀錄總判決頁數，處理頁數可能只有一頁的情況
    try:
        pages=int(re.findall(r'/\s(\d+)\s',soup.select('div.pull-right')[0].text)[0])
    except:
        pages=1
    
    #最多爬500筆資料(25頁)
    if pages>25:
        pages=25
    
    dfs=[]
    #抓取每頁判決表格
    for page in tqdm(range(1,pages+1)):
        link=url+'&sort=DS&page={}&ot=in'.format(page)
        response=requests.get(link,verify=False)
        try:
            df=pd.read_html(response.text)[0]
            Names=pd.Series([name]*len(df[df.index%2!=0]))
            Contents=df[df.index%2!=0]['裁判日期'].apply(lambda x:process_content(x)).reset_index(drop=True)
            Times=df[df.index%2==0]['裁判日期'].apply(lambda x:process_time(x)).reset_index(drop=True)
            Titles=df[df.index%2==0]['裁判字號 （內容大小）'].reset_index(drop=True)
            CaseNos=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:int(re.findall(r'第 (\d+) 號',x)[0])).reset_index(drop=True)
            Sizes=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:re.findall(r'（(\w+)）',x)[0]).reset_index(drop=True)
            Types=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:re.findall(r'號(\w{2})',x)[0]).reset_index(drop=True)
            Judges=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:re.findall(r'號\w{2}(\w{2})（',x)[0]).reset_index(drop=True)
            Words=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:re.findall(r'度\s(\w+)\s字',x)[0]).reset_index(drop=True)
            Courts=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:process_court(x)).reset_index(drop=True)
            Locations=df[df.index%2==0]['裁判字號 （內容大小）'].apply(lambda x:process_location(x)).reset_index(drop=True)
            Causes=df[df.index%2==0]['裁判案由'].reset_index(drop=True)
            
            #建立小表格
            df=pd.DataFrame({'name':Names,
                             'time':Times,
                             'location':Locations,
                             'court':Courts,
                             'caseNo':CaseNos,
                             'type':Types,
                             'judge':Judges,
                             'word':Words,
                             'cause':Causes,
                             'size':Sizes,
                             'title':Titles,
                             'content':Contents})
            dfs.append(df)
            time.sleep(0.5)
        except:
            None
    #合併成大表格
    df=pd.concat(dfs,ignore_index=True)
    #改成字典格式
    data_list=df.to_dict(orient='records')
        
    return df,data_list



#呼叫函數
if __name__ == '__main__':
    #抓取指定司法院裁判書關鍵字查詢結果
    df,data_list=law_crawler('蔡英文')
    #將指定司法院裁判書關鍵字查詢結果匯出成Excel檔
    df.to_excel('蔡英文.xlsx',index=False)
    #將指定司法院裁判書關鍵字查詢結果匯出成Json檔
    with open('蔡英文.json','w',encoding='utf8') as outfile:
        json.dump(data_list,outfile,ensure_ascii=False)




