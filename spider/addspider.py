import os
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin  # 用于处理相对路径链接


url = "http://oslab.mobisys.cc/" 


download_folder = "./downloads" 
os.makedirs(download_folder, exist_ok=True)  


response = requests.get(url)
html_content = response.content


html_file_path = os.path.join(download_folder, "page.html")
with open(html_file_path, 'wb') as html_file:
    html_file.write(html_content)
print(f"Original HTML page saved to {html_file_path}")

# 使用BeautifulSoup解析HTML页面
soup = BeautifulSoup(html_content, 'html.parser')

# 查找所有的<a>标签，获取所有下载链接
links = soup.find_all('a')

# 提取包含'pdf'、'zip'、'mp4'等的链接
download_links = []
for link in links:
    href = link.get('href')
    if href and (href.endswith('.pdf') or href.endswith('.zip') or 'video' in href):
        download_links.append(href)

# 输出所有的下载链接
for link in download_links:
    print(link)

# 下载文件并保存到指定位置
def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded {url} to {save_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

# 保存下载链接到CSV
csv_file = 'download_links.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['File Name', 'URL'])  # CSV表头
    
    for link in download_links:
        # 如果链接是相对路径，需要拼接成完整的URL
        full_url = urljoin(url, link) 

        # 获取文件名（例如从链接中提取文件名）
        file_name = full_url.split('/')[-1]
        save_path = os.path.join(download_folder, file_name)
        
        # 下载文件并保存
        download_file(full_url, save_path)
        
        # 写入CSV
        writer.writerow([file_name, full_url])

print(f"Download links have been saved to {csv_file}")
