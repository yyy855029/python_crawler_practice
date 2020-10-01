# coding: utf-8

#載入所需套件
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent import futures
from tqdm import tqdm
import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud


#定義爬取每篇中時政治新聞內容函數
def article_crawler(link_list):
    link=link_list[0]
    i=link_list[1]
    r=requests.get(link)
    s=BeautifulSoup(r.text,'html.parser')

    articlecontent=s.select('p')
    article=[e.text for e in articlecontent]
    #去除無意義內容
    article=article[:-3]

    return i,article


#定義爬取中時政治新聞資訊函數
def chinatimes_politics_crawler(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,'html.parser')
    
    entrys=soup.select('ul>li')
    titles,links,hours,dates=[],[],[],[]
    for e in entrys:
        try:
            titles.append(e.select('h3>a')[0].text)
            links.append('https://www.chinatimes.com{}'.format(e.select('h3>a')[0]['href']))
            hours.append(e.select('span.hour')[0].text)
            dates.append(e.select('span.date')[0].text)
        except:
            None

    articles=[0]*len(links)

    link_list=[]
    for i in range(len(links)):
        link_list.append([links[i],i])
    
    
    #進入每個連結爬取(執行thread層級的非同步任務)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results=list(tqdm(executor.map(article_crawler,link_list),total=len(link_list)))
        for future in results:
            i,article=future
            articles[i]=''.join(article)
            
    df=pd.DataFrame({
        '標題':titles,
        '日期':dates,
        '時間':hours,
        '內容':articles,
        '網址':links
    })    
    
    return df


#定義爬取多頁中時政治新聞資訊函數
def page_function(page):
    dfs=[]
    
    for i in range(page):
        url='https://www.chinatimes.com/realtimenews/260407?page={}&chdtv'.format(i+1)
        d=chinatimes_politics_crawler(url)
        dfs.append(d)
    
    df=pd.concat(dfs,ignore_index=True)
    
    return df


#抓取指定總頁數中時政治新聞資訊
df=page_function(8)
#將中時政治新聞資訊匯出成Excel檔
df.to_excel('中時政治新聞.xlsx',index=False)


#將新聞標題分詞
titles=df['標題'].values.tolist()
#'\u3000',' ','[^\w\s]','／','《','》','，','。','「','」','（','）','！','？','、','▲','…','：','...','-','︰','；','.'
text=''.join(titles).replace('\u3000','').replace(' ','').replace('[^\w\s]','').replace('／',"").replace('《','').replace('》','').replace('，','').replace('。','').replace('「','').replace('」','').replace('（','').replace('）','').replace('！','').replace('？','').replace('、','').replace('▲','').replace('…','').replace('：','').replace('...','').replace('-','').replace('︰','').replace('；','').replace('.','')

jieba.load_userdict('political.txt')
#精確模式
sentence=jieba.cut(text,cut_all=False)

#設定停用字
stopwords={}.fromkeys(['也','但','來','個','再','的','和','是','有','更','會','可能','有何',
                       '從','對','就','越','為','這種','多','越','要','在','把','於','以','間',
                       '應','與','了','你','我','他','沒','不要','事','被','嗎','說','都'])

#統計字詞頻率
hash={}
for item in sentence:
    if item in stopwords:
        continue    
    if item in hash:
        hash[item]+=1
    else:
        hash[item]=1

#繪製文字雲
wc=WordCloud(font_path='simsun.ttc',
             background_color='white',
             max_words=2000,
             stopwords=stopwords)
wc.generate_from_frequencies(hash)

plt.figure(figsize=(10,5))
#雙線性插值法
plt.imshow(wc,interpolation='bilinear')
plt.axis('off')
plt.savefig('中時政治新聞網文字雲.png')
plt.show()


#詞頻表格呈現
artdf=pd.DataFrame.from_dict(hash,orient='index',columns=['詞頻'])
print(artdf.sort_values(by=['詞頻'],ascending=False).head(15))


