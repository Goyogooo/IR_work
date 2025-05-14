from flask import Blueprint, render_template, session, redirect, url_for
from app.utils.search import main
from database.models import SearchHistory
import time,os
from datetime import datetime  # Add this line to import the datetime module
import pandas as pd
front = Blueprint('front', __name__)

# 获取当前脚本文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 项目根目录（两级上层：从 routes/search_routes.py 到 project 根目录）
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 定位 title_url_desc.csv 的路径
csv_path = os.path.join(project_root, "title_url_desc.csv")

url_title_desc = pd.read_csv(csv_path, encoding='utf-8-sig', index_col='url')
            


# 获取特定关键词的查询时间戳
def get_search_timestamp(user_id, keyword):
    # 假设 SearchHistory 是一个数据库模型，包含 user_id, keyword 和 timestamp 字段
    search_history_record = SearchHistory.query.filter_by(user_id=user_id, keyword=keyword).first()
    
    if search_history_record:
        return search_history_record.timestamp  # 返回查询时间戳
    else:
        return None  # 如果没有找到该关键词的查询记录，返回 None

# 获取用户历史记录，最多3条
def get_user_history(user_id):
    search_history_records = SearchHistory.query.filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).limit(1).all()
    return [record.keyword for record in search_history_records]
    
def get_search_results_based_on_history(user_id):
    # 获取用户历史记录，仅保留最近3条
    search_history = get_user_history(user_id) # 取最近3条关键词
    # search_history = get_user_history(user_id)  # 获取历史搜索关键词
    if not search_history:
        results = []
    else:
        results = []
        for keyword in search_history:
            result_list = main(input_word=keyword, history_words=search_history, is_title_only=False)  # 基于历史关键词查询
            if not result_list:
                continue  # 如果没有查询到结果，则跳过该条记录
            weighted_results = []
            
            # 给每个结果加上时间加权得分
            for result in result_list:
                url, similarity = result
                # 假设越近的时间加权越高，可以根据历史查询时间来加权
                timestamp = get_search_timestamp(user_id, keyword)  # 获取该关键词的查询时间
                weight = calculate_weight(timestamp)  # 根据时间计算权重
                weighted_results.append((url, similarity * weight))
            
            # 按加权得分排序
            weighted_results.sort(key=lambda x: x[1], reverse=True)
            results.extend(weighted_results[:10])  # 取前10条结果
        
    return results

def calculate_weight(timestamp):
    if not timestamp:
        return 0  # 如果没有时间戳，权重为 0
    if not timestamp:
        return 0.1  # 默认较低权重
    current_time = datetime.fromtimestamp(time.time())
    time_diff = current_time - timestamp  # 时间差对象
    seconds = time_diff.total_seconds()
    
    # 使用对数函数加权：秒数越小，权重越高
    if seconds < 60:  # 1分钟以内
        return 5.0
    elif seconds < 3600:  # 1小时以内
        return 2.0 + (1 / (seconds / 60))  # 2.0基础权重，加上分钟倒数
    elif seconds < 86400:  # 1天以内
        return 1.0 + (1 / (seconds / 3600))  # 1.0基础权重，加上小时倒数
    else:  # 超过1天
        return max(0.5, 1 / (seconds / 86400))  # 最低权重0.5

def get_top_recommended_results(user_id):
    # 获取用户的历史记录
    current_history = get_user_history(user_id)  # 获取最新的历史记录

    # 检查用户是否已经有缓存的推荐结果
    if 'recommended_results' in session and session['user_id'] == user_id:
        last_updated = session.get('history_last_updated', None)

        # 如果历史记录没有变化，则返回缓存的推荐结果
        if last_updated and current_history == session['history_last_updated']:
            return session['recommended_results']
        
    all_results = get_search_results_based_on_history(user_id)  # 获取基于历史查询的结果
    top_results = sorted(all_results, key=lambda x: x[1], reverse=True)[:5]  # 取前5个


    recommended_results = []
    for url, score in top_results: 
        temp_series = url_title_desc.loc[url].fillna('')
        title = temp_series['title'].replace('_', '/') if 'title' in temp_series else "Unknown Title"
        recommended_results.append({"title": title, "url": url, "score": round(score, 4)})
    
    # 将推荐结果保存到 session 中
    session['recommended_results'] = recommended_results
    session['history_last_updated'] = current_history  # 保存历史记录的最新状态

    return recommended_results

@front.route('/')
def index():
    """
    项目首页
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))  # 未登录跳转到登录页面

    # 获取基于历史查询的个性化推荐
    recommended_results = get_top_recommended_results(user_id)  

    return render_template('index.html', recommended_results=recommended_results)
