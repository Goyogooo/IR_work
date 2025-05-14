import os 
import asyncio
import aiofiles
import httpx
from parsel import Selector
import pandas as pd
import re
from yarl import URL  # 使用 yarl 包处理 URL

# 存储标题和 URL 的 DataFrame
title_url_df = pd.DataFrame(columns=['url'])
title_url_df.index.name = 'title'


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 定义跳转提示的关键词，页面标题包含这些词的将被舍弃
jump_keywords = ['跳转', 'Redirect', '提示', '请稍后', '页面正在跳转']

# 清理文件名中的非法字符
def clean_filename(title):
    """清理文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def make_absolute_url(base_url, relative_url):
    """生成完整的 URL，拼接基础 URL 和相对路径"""
    # 确保 base_url 是字符串并且没有多余的斜杠
    if isinstance(base_url, str):
        base_url = base_url.rstrip('/')
    else:
        raise ValueError(f"Expected 'base_url' to be a string, got {type(base_url)}")

    # 如果相对路径已经是完整的 URL，则直接返回
    if relative_url.startswith('http') or relative_url.startswith('https'):
        return relative_url
    # 如果相对路径以'/'开始，拼接基础 URL 和路径
    elif relative_url.startswith('/'):
        return base_url + relative_url
    else:
        # 否则拼接路径部分
        return base_url + '/' + relative_url

async def save_resource(url, resource_type, base_dir, title, base_url):
    try:
        # 确保 URL 是完整的
        full_url = make_absolute_url(base_url, url)
        # print(f"Downloading {resource_type} from {full_url}")  # 输出正在下载的资源信息

        resource_dir = os.path.join(base_dir, "resources", title)
        if not os.path.exists(resource_dir):
            os.makedirs(resource_dir)

        resource_name = clean_filename(os.path.basename(full_url))  # 处理文件名中的非法字符
        resource_path = os.path.join(resource_dir, resource_name)

        # 下载资源并保存
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, headers=headers)
            if response.status_code == 200:
                async with aiofiles.open(resource_path, 'wb') as f:
                    await f.write(response.content)
                # print(f"{resource_type.capitalize()} saved: {resource_path}")
            else:
                print(f"Failed to download {resource_type}: {full_url}, Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {resource_type} {url}: {e}")

async def download_page_resources(url, base_dir, title, base_url):
    """下载页面中的图片、CSS 和 JS 文件"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10)
        selector = Selector(response.text)

        # 下载图片
        img_urls = selector.css('img::attr(src)').getall()
        for img_url in img_urls:
            await save_resource(img_url, 'image', base_dir, title, base_url)

        # 下载 CSS 文件
        css_urls = selector.css('link[rel="stylesheet"]::attr(href)').getall()
        for css_url in css_urls:
            await save_resource(css_url, 'css', base_dir, title, base_url)

        # 下载 JS 文件
        js_urls = selector.css('script[src]::attr(src)').getall()
        for js_url in js_urls:
            await save_resource(js_url, 'js', base_dir, title, base_url)

async def update_html_with_local_resources(html_content, base_dir, title, base_url):
    """修改 HTML 文件中的资源路径为本地路径"""
    selector = Selector(html_content)

    # 修改图片路径
    img_urls = selector.css('img::attr(src)').getall()
    for img_url in img_urls:
        local_img_url = make_absolute_url(base_url, img_url)
        html_content = html_content.replace(img_url, local_img_url)

    # 修改 CSS 路径
    css_urls = selector.css('link[rel="stylesheet"]::attr(href)').getall()
    for css_url in css_urls:
        local_css_url = make_absolute_url(base_url, css_url)
        html_content = html_content.replace(css_url, local_css_url)

    # 修改 JS 路径
    js_urls = selector.css('script[src]::attr(src)').getall()
    for js_url in js_urls:
        local_js_url = make_absolute_url(base_url, js_url)
        html_content = html_content.replace(js_url, local_js_url)

        # 如果 JS 文件是 jQuery 的路径，特别处理
        if "jquery" in js_url.lower():
            local_js_url = make_absolute_url(base_url, js_url)
            html_content = html_content.replace(js_url, local_js_url)

    return html_content

async def save_page(url, client, base_dir):
    """保存网页内容并下载资源"""
    try:
        response = await client.get(url, headers=headers, timeout=10)
        print(f"Requesting {url}...")  # 确保这个输出在请求之前
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Request failed for {url}, Status Code: {response.status_code}")
            return None, None  # 请求失败，返回 None

        selector = Selector(response.text)

        # 提取标题
        title = selector.css('title::text').get()
        if not title:
            print(f"Failed to extract title from {url}")
            return None, None

        # 判断标题是否包含跳转提示关键词
        if any(keyword in title for keyword in jump_keywords):
            print(f"Skipping page due to jump or redirect prompt: {title}")
            return None, None  # 如果标题包含跳转提示，跳过该页面

        # 清理文件名中的非法字符
        title = clean_filename(title)

        # 获取 base_url（基础 URL）
        base_url = 'https://zyfw.nankai.edu.cn'
        # print(f"Base URL: {base_url}")  # 调试输出 base_url，确认其类型

        # 保存 HTML 页面
        html_filepath = os.path.join(base_dir, f"{title}.html")
        async with aiofiles.open(html_filepath, 'w', encoding='utf-8') as f:
            await f.write(response.text)

        # 下载页面中的资源
        await download_page_resources(url, base_dir, title, base_url)

        # 修改 HTML 文件中的资源路径为本地路径
        with open(html_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        updated_html = await update_html_with_local_resources(html_content, base_dir, title, base_url)

        # 将更新后的 HTML 保存回文件
        async with aiofiles.open(html_filepath, 'w', encoding='utf-8') as f:
            await f.write(updated_html)

        # 将标题和 URL 保存到 DataFrame 中
        title_url_df.loc[title] = url
        print(f"Saved: {title} from {url}")
        
        return title, url

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None, None

     
async def main():
    page_ids = range(7001,11000)  

    # 生成每个页面的 URL
    url_list = [f'https://zyfw.nankai.edu.cn/index/newsview/id/{i}.aspx' for i in page_ids]

    # 确保保存页面的目录存在
    base_dir = './news_saved_pages'
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    # 创建 HTTPX 客户端
    async with httpx.AsyncClient() as client:
        # 顺序访问，每次一个请求
        for url in url_list:
            await save_page(url, client, base_dir)

    # 将标题和 URL 映射保存为 CSV 文件（CSV 文件与 saved_pages 文件夹在同一目录）
    title_url_df.to_csv("./news_title_url.csv", mode='a', header=not os.path.exists("./news_title_url.csv"))
    print("Saved title_url.csv")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
