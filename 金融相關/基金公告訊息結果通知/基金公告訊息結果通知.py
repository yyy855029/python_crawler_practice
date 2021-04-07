# coding: utf-8

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime,timedelta
import win32com.client as win32 


#定義函數
def fund_information_crawler():
    now=datetime.now()
    #上週星期一和星期五
    last_monday=now-timedelta(days=now.weekday()+7)  
    last_friday=now-timedelta(days=now.weekday()+3) 
    last_monday_str=datetime.strftime(last_monday,'%Y/%m/%d')
    last_friday_str=datetime.strftime(last_friday,'%Y/%m/%d')

    headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
    }

    data={
        'dateType':'0',
        'startDateTime':last_monday_str,
        'endDateTime':last_friday_str,
        'query':'1'
    }

    companys=[]
    funds=[]
    dates=[]
    informations=[]

    session=requests.Session()
    first_url='https://futures-announce.fundclear.com.tw/FMA/app/MSG010'
    response=session.get(first_url,headers=headers)
    #先從初始連結取得interface參數值
    inter_num=re.findall(r'=:(\d+):',response.text)[0]

    second_url='https://futures-announce.fundclear.com.tw/FMA/app/?wicket:interface=:{}:queryForm:query:-1:IUnversionedBehaviorListener&wicket:behaviorId=0&wicket:ignoreIfNotActive=true'.format(inter_num)
    response=session.post(second_url,headers=headers,data=data)
    
    try:
        #餵入日期後取得總頁數
        page_num=int(re.findall(r'共\s*(\d+)\s*頁',response.text)[0])

        for num in range(page_num):
            #進入每頁連結取得資料
            url='https://futures-announce.fundclear.com.tw/FMA/app/?wicket:interface=:{}:grid:managerForm:checkGroup:dataGrid:bottomToolbars:4:toolbar:span:navigator:navigation:{}:pageLink::IBehaviorListener&wicket:behaviorId=0'.format(inter_num,num)
            response=session.get(url,headers=headers)
            soup=BeautifulSoup(response.text,'lxml')
            page_data=soup.select('td')[:-1]

            for i in range(0,len(page_data),4):
                companys.append(page_data[i].text.replace('\n',''))
                funds.append(page_data[i+1].text.replace('\n',''))
                dates.append(page_data[i+2].text.replace('\n',''))
                info=page_data[i+3].text.replace('\n','')
                link='https://futures-announce.fundclear.com.tw'+page_data[i+3].select('a')[0]['href']
                #HTML超連結設定
                informations.append('<a href="{}">{}</a>'.format(link,info))
    
    except:
        #查無結果例外
        pass
    
    df=pd.DataFrame({
        '期信事業':companys,
        '基金名稱':funds,
        '申報日期':dates,
        '訊息內容':informations
    })  

    return df



def send_mail(df):
    addressee_list=['xxx@xxx.com.tw','yyy@yyy.com.tw'] 
    addressee=';'.join(addressee_list)
    date=datetime.now()
    date_str=datetime.strftime(date,'%Y%m%d')
    #HTML表格超連結設定
    content=\
    """
    <body>
    
    <div class="content">
        <h2>查詢網址 :</h2>
        <a href="https://futures-announce.fundclear.com.tw/FMA/app/MSG010">https://futures-announce.fundclear.com.tw/FMA/app/MSG010</a>
        <br>
        <h2>結果 :</h2>
        {}
    </div>
    
    </body>
    
    """.format(df.to_html(index=False,
                          render_links=True,
                          escape=False))    

    #寄送信件
    outlook=win32.Dispatch('outlook.application') 
    mail=outlook.CreateItem(0) 
    mail.To=addressee
    mail.Subject='[測試] {}_上週基金公告訊息'.format(date_str)
    mail.HTMLBody=content 
    mail.Send() 
    


#呼叫函數
if __name__ == '__main__':
    df=fund_information_crawler()
    send_mail(df)









