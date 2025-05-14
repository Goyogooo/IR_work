# !/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import os
import re
import asyncio
import aiofiles
import pandas as pd
import networkx
from parsel import Selector
from jieba import cut_for_search

analyzer = cut_for_search 

title_url_df = pd.read_csv("./cleaned_title_url.csv", index_col=0)

index_df = pd.DataFrame(columns=['title', 'description', 'content', 'editor'])
index_df.index.name = 'url'

sem = asyncio.Semaphore(30)  # 设置协程数，这边都是本地IO，所以可以设置较高的协程数

punctuation_cn = '＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､\u3000、〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。'  # 中文标点符号集合，用于去除中文标点符号

url_url_list_dict = {}  # 用于存储以URL为索引的，每个URL中包含的URL的列表

# analyzer：指定中文分词器，用于分词操作。
# title_url_df：通过Pandas读取一个CSV文件，包含标题和URL的对应关系。这个文件用来从爬取的页面中找到真实的URL。
# index_df：一个空的Pandas DataFrame，用来存储每个页面的索引信息，包括标题、描述、时间戳、正文内容和编辑信息。
# sem：一个Semaphore（信号量），用于控制并发协程的数量，防止并发数过高导致资源消耗过大。这里设置为30。
# punctuation_cn：一个包含所有中文标点符号的字符串，用于后续文本处理时去除标点符号。
# url_url_list_dict：一个字典，用于存储每个URL对应的所有页面链接，帮助计算PageRank。

unmatched_df = pd.DataFrame(columns=['html_file', 'title'])
unmatched_df.index.name = 'index'

async def create_index(file):
    async with sem:
        try:
            async with aiofiles.open(file, mode='r', encoding='utf-8') as f:
                text = await f.read()
                selector = Selector(text)
                title = selector.css('title::text').get()
                _title = title.replace('/', '_')

                try:
                    url = title_url_df.loc[_title, 'url'] 
                except KeyError:
                    print(f"Title not found in CSV: {_title}")
                    unmatched_df.loc[len(unmatched_df)] = [file, _title]  
                    return  
                
                description = selector.css('meta[name="description"]::attr(content)').get()  # 获取head内的description
                if description is not None:  
                    description = description.replace('\r', '').replace('\n', '').replace('\t', '').replace('\n', '').replace('　', '')
                title_url_df.loc[_title, 'description'] = description
            
                _content: list = selector.css('td::text, p::text').getall()

                content = "".join(_content[:-1])  
                if _content != []:  
                    content = content.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', ' ').replace('　', '')
                    try:
                        editor = _content[-1].replace('\n', '').replace(' ', '')
                    except:
                        print(content, _content) 
                        exit()
                else:
                    editor = None

           
                title = list(analyzer(title))
                if description is not None:
                    description = list(analyzer(description))
                if description is not None:
                    content = list(analyzer(content))

              
                title = (re.sub(rf"[{punctuation_cn}]", '', '✘'.join(title)).replace('-', '')).split('✘')  # 标题需要额外删除用于SEO的-符号
                title = ' '.join([word for word in title if (word != '' and word != ' ')])
                if description is not None:
                    description = re.sub(rf"[{punctuation_cn}]", '', '✘'.join(description)).split('✘')
                    description = ' '.join([word for word in description if (word != '' and word != ' ')])
                if content is not None:
                    content = re.sub(rf"[{punctuation_cn}]", '', '✘'.join(content)).split('✘')
                    content = ' '.join([word for word in content if (word != '' and word != ' ')])

               
                index_df.loc[url] = [title, description, content, editor]


                # 提取页面中的url
                url_list = []
                url_list.extend(selector.css('a::attr(href)').getall())
                url_url_list_dict[url] = url_list

        except Exception as e:
            print(f"Error processing file {file}: {e}")
            unmatched_df.loc[len(unmatched_df)] = [file, 'Unknown Title']

async def main():
    files = os.listdir('./2pages')  
    
    files = [
        file for file in files
        if not os.path.isdir(f'./2pages/{file}') or file != 'resources'
    ]
    tasks = [asyncio.create_task(create_index(f'./2pages/{file}')) for file in files]
    await asyncio.gather(*tasks)

 
    index_df.to_csv("./index.csv", encoding='utf-8-sig')

   
    unmatched_df.to_csv("./unmatched_pages.csv", encoding='utf-8-sig')

    # 计算PageRank
    digraph = networkx.DiGraph()
    for url, url_list in url_url_list_dict.items():
        for _url in url_list:
            if _url in title_url_df.url.values:
                digraph.add_edge(url, _url)
    result = networkx.pagerank(digraph, alpha=0.85)
    page_rank_df = pd.Series(result, name='page_rank')
    page_rank_df = page_rank_df.apply(lambda x: math.log(x * 10000, 10) + 1)  
    page_rank_df.index.name = 'url'
    page_rank_df.to_csv("./page_rank.csv", encoding='utf-8-sig')
    title_url_df.to_csv("./title_url_desc.csv", encoding='utf-8-sig') 


if __name__ == '__main__':
    # asyncio.run(main())
    loop = asyncio.get_event_loop()  # 获取当前事件循环
    loop.run_until_complete(main())  # 显式运行主任务
