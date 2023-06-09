# coding: utf-8

#載入所需套件
import requests
import pandas as pd
import time
from tqdm import tqdm
import json


#定義抓取可能免費IP清單函數
def possible_ip_crawler():
    url_list=['https://www.us-proxy.org/','https://free-proxy-list.net/']
    possible_ip_list=[]
    
    for url in tqdm(url_list):
        response=requests.get(url)
        df=pd.read_html(response.text)[0]
        df.drop((len(df)-1),axis=0,inplace=True)
        df['Port']=df['Port'].apply(lambda x:str(int(x)))
        df['IP']=df['IP Address']+':'+df['Port']
        ip_list=df['IP'].values
        possible_ip_list.extend(ip_list)
    
    possible_ip_list=list(set(possible_ip_list))
    
    return possible_ip_list


#定義檢驗可能免費IP清單函數
def test_possible_ip(possible_ip_list):
    test_url='https://api.ipify.org?format=json'
    response=requests.get(test_url)
    raw_ip=response.json()['ip']
    
    ip_dict_list=[]
    for e in tqdm(possible_ip_list):
        proxies={'http':e,'https':e}
        time.sleep(0.5)
        try:
            response=requests.get(test_url,proxies=proxies,timeout=5)
            if response.json()['ip']!=raw_ip:
                ip_dict_list.append(proxies)
            else:
                pass
        except:
            pass
    
    return ip_dict_list



#呼叫函數
if __name__ == '__main__':
    #抓取可能免費IP清單
    possible_ip_list=possible_ip_crawler()
    #檢驗可能免費IP清單
    ip_dict_list=test_possible_ip(possible_ip_list)
    print('可用免費ip比例 : {}/{}={:4.2f}%'.format(len(ip_dict_list),len(possible_ip_list),(len(ip_dict_list)/len(possible_ip_list))*100))
    #儲存可用免費IP清單成Json檔
    with open('./可用免費ip清單.json','w') as f:
        json.dump(ip_dict_list,f)







