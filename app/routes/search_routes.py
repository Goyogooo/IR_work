from flask import Blueprint, render_template, request, redirect, url_for, Response, session
from database.models import db, SearchHistory
from app.utils.search import main
from search.config import *
import time
from flask import current_app
import os
import csv
# 获取当前脚本文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))


project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 定位 title_url_desc.csv 的路径
csv_path = os.path.join(project_root, "title_url_desc.csv")

search_bp = Blueprint('search', __name__)




# 判断关键词是否为文档
def is_document(keyword):
    document_extensions = ['.pdf', '.docx', '.txt', '.pptx', '.zip', '.html']
    file_extension = os.path.splitext(keyword)[-1].lower()  # 获取文件后缀
    return file_extension in document_extensions  # 判断是否为文档类型

# 假设CSV文件包含文档的名称和URL
CSV_FILE = os.path.join(project_root, "download_links.csv")

def search_documents(keyword):
    documents = []
    # 如果是文档，直接查找CSV中对应的文件
    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过表头
        for row in reader:
            file_name, file_url = row
            if keyword.lower() in file_name.lower():
                documents.append({
                    'file_name': file_name,
                    'file_url': file_url,
                })

    return documents

@search_bp.route('/basic_search',methods=['GET','POST'])
def search_page():
   
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('auth.login'))  # 用户未登录，跳转到登录页面

    
    # 获取用户的搜索历史（前 12 条）
    search_history_records = SearchHistory.query.filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).limit(12).all()
    search_history = [record.keyword for record in search_history_records]

    if request.method == 'POST':
        keywords = request.form.get('keywords')  # 获取表单中的关键词
        
        if is_document(keywords):
            documents = search_documents(keywords)  # 获取文档信息
            new_history = SearchHistory(user_id=user_id, keyword=keywords)
            db.session.add(new_history)
            db.session.commit()
           
            if documents:   
                return render_template('doc_results.html', documents=documents, keyword=keywords)
            else:
                return render_template('doc_results.html', documents=[], keyword=keywords)
        
        search_mode = request.form.get('search_mode')  # 获取搜索模式
        is_title_only = search_mode == 'title'  # 判断是否是标题搜索
        
        if not keywords:
            return redirect(url_for('front.index'))  # 如果没有输入关键词，跳转到首页

        # 调用搜索逻辑并处理历史记录
        t = time.perf_counter()  # 计时
        try:
            # 执行搜索
            current_app.logger.debug("Calling main function with keywords: %s, history: %s, is_title_only: %s", keywords, search_history, is_title_only)
            result_list = main(keywords, search_history,is_title_only=is_title_only)
            url_title_desc = pd.read_csv(csv_path, encoding='utf-8-sig', index_col='url')
            results = []
            for url, similarity in result_list:
                # 检查 URL 是否存在于 url_title_df
                if url not in url_title_desc.index:
                    current_app.logger.warning("Skipping URL not found in index: %s", url)
                    continue  # 跳过不存在的 URL
                # 假设我们从一个字典中获取标题和描述
                temp_series = url_title_desc.loc[url].fillna('')
                title = temp_series['title'].replace('_', '/') if 'title' in temp_series else "Unknown Title"
                description = temp_series['description'] if 'description' in temp_series else "No Description"
                page_rank_score = page_rank_df.loc[url]['page_rank'] if url in page_rank_df.index else 1.0
                weighted_score = similarity * page_rank_score
                results.append((title, url, description, weighted_score))  # 加权计算结果

            results.sort(key=lambda x: x[3], reverse=True)

        except KeyError as e:
            current_app.logger.error("Error occurred during search: %s", str(e))
            results = []
            current_app.logger.warning("No valid results found for the given keywords.")
            
        # 更新搜索历史
       
        new_history = SearchHistory(user_id=user_id, keyword=keywords)
        db.session.add(new_history)
        db.session.commit()

        cost_time = f'{time.perf_counter() - t: .2f}'
        
           
        return render_template(
            'result_page.html',  # 结果展示页面
            keywords=keywords,
            results=results,
            len_results=len(results),
            cost_time=cost_time,
            search_history=search_history,
            no_result_message=f"没有找到与 '{keywords}' 相关的结果。" if not results else None
        )

    # 如果是 GET 请求，则展示搜索页面
    return render_template('base_search.html', search_history=search_history)