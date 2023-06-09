# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


#定義爬取中職球員數據函數
def cpbl_data_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')

    items=[e.text for e in soup.select('th')]
    datas=[e.text for e in soup.select('td')]
    datas=[datas[j:j+31] for j in range(0,len(datas),31)]

    df=pd.DataFrame(datas,columns=items)
    
    return df   

#定義爬取多頁中職球員數據函數
def page_function(page):
    dfs=[]
    
    for i in tqdm(range(1,page+1)):
        url='http://www.cpbl.com.tw/stats/all.html?year=0000&stat=pbat&online=0&sort=G&order=desc&per_page={}'.format(i)
        d=cpbl_data_crawler(url)
        dfs.append(d)
    
    df=pd.concat(dfs,ignore_index=True)
    
    return df



#呼叫函數
if __name__ == '__main__':
    #抓取指定總頁數中職球員數據
    df=page_function(10)
    #將中職球員數據匯出成Excel檔
    df.to_excel('中職數據排名資料.xlsx',index=False)




