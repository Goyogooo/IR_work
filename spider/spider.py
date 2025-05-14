# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import asyncio
import aiofiles

import pandas as pd
import httpx
from parsel import Selector
import requests
# 设置事件循环策略
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 


url_list = [f'https://zyfw.nankai.edu.cn/index/diary/p/2.aspx']


aaa = 1
# 自动跟随重定向
for url in url_list:
    response = requests.get(url, allow_redirects=True)
    print(aaa)
    aaa=aaa+1

sem = asyncio.Semaphore(10)  
result_dict = {}

title_url_df = pd.DataFrame(columns=['url'])
title_url_df.index.name = 'title'


async def parse_catalogs_page(url):
    async with sem:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            # 打印响应状态码
            print(f"Requested {url} with status code: {response.status_code}")
            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                return
            selector = Selector(response.text)
            temp_dict = zip(selector.css('a::attr(href)').getall(), selector.css('a::text').getall())
            result_dict.update(temp_dict)
            print(f"Catalog page parsed: {url}")


async def parse_page(url):
    async with sem:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10,
                                         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}) as client:
                                         
                if url.startswith('http') or url.startswith('https'):
                    response = await client.get(url)
                    # 打印响应状态码
                    # print(f"Requested {url} with status code: {response.status_code}")
                    if response.status_code != 200:
                        print(f"Failed to fetch {url}")
                        return
                    selector = Selector(response.text)
                    title = selector.css('title::text').get()
                    # 打印标题以确认获取成功
                    print(f"Parsed title: {title}")
                    try:
                        if "/" in title:
                            title = title.replace("/", "_")
                        async with aiofiles.open(f'./2pages/{title}.html', mode='a', encoding='utf-8') as f:
                            await f.write(response.text)
                        title_url_df.loc[title] = url  # 建立标题和url的映射关系

                    except Exception as e:
                        print(f'{e}: {url}|{title}')
        except:
            print(f'error: {url}')


async def main():
    # 检查pages文件夹是否存在，不存在则创建
    if not os.path.exists('./2pages'):
        os.mkdir('./2pages')

    tasks = [asyncio.create_task(parse_catalogs_page(url)) for url in url_list]
    await asyncio.gather(*tasks)

    tasks = [asyncio.create_task(parse_page(url)) for url in result_dict.keys()]
    await asyncio.gather(*tasks)

    title_url_df.to_csv("./2title_url.csv", mode='a', header=not os.path.exists("./2title_url.csv"))
    print("Saved 2title_url.csv")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())