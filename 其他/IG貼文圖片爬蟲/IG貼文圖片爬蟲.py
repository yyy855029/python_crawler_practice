# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import json
from urllib.request import urlretrieve
import re
from tqdm import tqdm
import numpy as np
import pandas as pd
import time
from datetime import datetime
import os


#定義爬取IG帳號基本資訊函數
def ig_summary_crawler(id_name):
    header={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
    url='https://www.instagram.com/{}/'.format(id_name)
    response=requests.get(url,headers=header)
    soup=BeautifulSoup(response.text,'lxml')
    json_part=soup.find_all('script',type='text/javascript')[3].string
    json_part=json_part[json_part.find('=')+2:-1]
    data=json.loads(json_part)
    user_data=data['entry_data']['ProfilePage'][0]['graphql']['user']

    user_id=user_data['id']
    full_name=user_data['full_name']
    biography=user_data['biography']
    followed_num=user_data['edge_followed_by']['count']
    follow_num=user_data['edge_follow']['count']
    entry_num=user_data['edge_owner_to_timeline_media']['count']

    summary_df=pd.DataFrame({
        '編號':user_id,
        '名稱':full_name,
        '簡介':biography,
        '被追蹤數':followed_num,
        '追蹤數':follow_num,
        '貼文數':entry_num
    },index=[0])
    
    directory='IG圖片爬蟲/{}'.format(id_name)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    
    summary_df.to_csv('{}/{}個人簡介.csv'.format(directory,id_name),encoding='utf_8_sig',index=False)
    
    return summary_df,entry_num,user_id


#定義爬取IG帳號貼文、圖片函數
def user_data_crawler(url):
    header={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
    response=requests.get(url,headers=header)
    
    try:
        soup=BeautifulSoup(response.text,'lxml')
        json_part=soup.find_all('script',type='text/javascript')[3].string
        json_part=json_part[json_part.find('=')+2:-1]
        data=json.loads(json_part)
        user_data=data['entry_data']['ProfilePage'][0]['graphql']['user']
    except:
        #處理第2頁以後user_data的json格式不同
        user_data=json.loads(response.text)['data']['user']
    
    return user_data


def ig_img_page_crawler(user_data):
    one_page_info=user_data['edge_owner_to_timeline_media']['edges']

    texts=[]
    tags=[]
    ats=[]
    img_links=[]
    post_links=[]
    tag_nums=[]
    at_nums=[]
    img_nums=[]
    message_nums=[]
    heart_nums=[]
    ids=[]
    post_times=[]
    locations=[]

    #每個one_page_info首頁最多有12篇，第2頁以後每頁最多有50篇
    for i in range(len(one_page_info)):
        img_link=[]
        try:
            text=one_page_info[i]['node']['edge_media_to_caption']['edges'][0]['node']['text']
            texts.append(text)
            #抓取ig貼文#
            if '#' in text:
                tag_list=re.findall(r'#([^ |\n]+)',text)
                tag_nums.append(len(tag_list))
                tags.append('\n'.join(tag_list))
            else:
                tag_nums.append(0)
                tags.append('')
            #抓取ig貼文@
            if '@' in text:
                at_list=re.findall(r'@([^ |\n]+)',text)
                at_nums.append(len(at_list))
                ats.append('\n'.join(at_list))
            else:
                at_nums.append(0)
                ats.append('')
        except:
            #處理ig貼文沒文字敘述情況
            texts.append('')
            tag_nums.append(0)
            tags.append('')
            at_nums.append(0)
            ats.append('')
        try:
            #處理ig貼文可能不只1張圖片情況
            img_info=one_page_info[i]['node']['edge_sidecar_to_children']['edges']
            img_num=len(img_info)
            img_nums.append(img_num)
            
            for j in range(img_num):
                img_link.append(img_info[j]['node']['display_url'])
            img_links.append(img_link)
        except:
            img_nums.append(1)
            img_links.append(one_page_info[i]['node']['display_url'])
        try:
            locations.append(one_page_info[i]['node']['location']['name'])
        except:
            #處理ig貼文沒打卡地點情況
            locations.append('')
        
        message_nums.append(one_page_info[i]['node']['edge_media_to_comment']['count'])
        heart_nums.append(one_page_info[i]['node']['edge_media_preview_like']['count'])
        ids.append(one_page_info[i]['node']['id'])
        int_time=one_page_info[i]['node']['taken_at_timestamp']
        post_times.append(datetime.fromtimestamp(int_time).strftime('%Y-%m-%d %H:%M:%S'))
        post_code=one_page_info[i]['node']['shortcode']
        post_links.append('https://www.instagram.com/p/{}/'.format(post_code))
        
    img_df=pd.DataFrame({
        '編號':ids,
        '時間':post_times,
        '貼文':texts,
        '標籤':tags,
        '標註':ats,
        '打卡地點':locations,
        '留言數':message_nums,
        '愛心數':heart_nums,
        '標籤數':tag_nums,
        '標註數':at_nums,
        '圖片數':img_nums,
        '貼文網址':post_links,
        '圖片網址':img_links 
    })        

    return img_df


def ig_img_total_crawler(entry_num,user_id,id_name):
    img_dfs=[]
    url='https://www.instagram.com/{}/'.format(id_name)
    user_data=user_data_crawler(url)
    img_df=ig_img_page_crawler(user_data)
    img_dfs.append(img_df)
    next_code=user_data['edge_owner_to_timeline_media']['page_info']['end_cursor']
    
    #首頁最多有12篇，第2頁以後每頁最多50篇
    if (entry_num-12)%50==0:
        iter_times=int((entry_num-12)/50)
    else:
        iter_times=int((entry_num-12)/50)+1
    
    for i in tqdm(range(iter_times)):
        url='https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a&variables=%7B%22id%22%3A%22{}%22%2C%22first%22%3A50%2C%22after%22%3A%22{}%3D%3D"%7D'.format(user_id,next_code.replace('=',''))
        time.sleep(0.5)
        user_data=user_data_crawler(url)
        img_df=ig_img_page_crawler(user_data)
        img_dfs.append(img_df)
        next_code=user_data['edge_owner_to_timeline_media']['page_info']['end_cursor']
    
    total_img_df=pd.concat(img_dfs,ignore_index=True)
    
    directory='IG圖片爬蟲/{}'.format(id_name)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    
    total_img_df.to_csv('{}/{}貼文資訊.csv'.format(directory,id_name),encoding='utf_8_sig',index=False)
    
    return total_img_df


#定義下載儲存IG帳號圖片、貼文檔案函數
def download_img_text(id_name,total_img_df):
    for i in tqdm(range(len(total_img_df))):
        directory='IG圖片爬蟲/{}/{}'.format(id_name,i)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        
        text=total_img_df.loc[i,'貼文']
        tag=total_img_df.loc[i,'標籤']
        at=total_img_df.loc[i,'標註']
        img_links=total_img_df.loc[i,'圖片網址']
        
        with open('{}/貼文.txt'.format(directory),'w',encoding='utf-8') as f:
            f.write(text) 
        
        with open('{}/標籤.txt'.format(directory),'w',encoding='utf-8') as f:
            f.write(tag) 
            
        with open('{}/標註.txt'.format(directory),'w',encoding='utf-8') as f:
            f.write(at) 
        
        try:
            for j in range(len(img_links)):
                urlretrieve(img_links[j],'{}/{}.png'.format(directory,j))
        except:
            urlretrieve(img_links,'{}/{}.png'.format(directory,0))



#呼叫函數
if __name__ == '__main__':
    #特定IG公開帳號爬蟲
    id_name=input('請輸入IG帳號 : ')
    try:
        summary_df,entry_num,user_id=ig_summary_crawler(id_name)
        print('輸入的IG帳號為：{}，共有{}篇貼文'.format(id_name,entry_num))
    except:
        print('此帳號輸入錯誤(或設定不公開)')
    try:
        total_img_df=ig_img_total_crawler(entry_num,user_id,id_name)
        print('圖片貼文表格下載成功')
    except:
        print('圖片貼文表格下載失敗')
    try:
        download_img_text(id_name,total_img_df)
        print('圖片貼文檔案下載成功')
    except:
        print('圖片貼文檔案下載失敗')





    