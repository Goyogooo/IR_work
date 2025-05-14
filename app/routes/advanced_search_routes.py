from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired
from flask import Blueprint, render_template, request, redirect, url_for, session
from database.models import db, SearchHistory
from app.utils.search_plus import main_func
from search.config import *
from flask import current_app
import time
import re
import os

advanced_search_bp = Blueprint('advanced_search', __name__)

# 获取当前脚本文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))


project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 定位 title_url_desc.csv 的路径
csv_path = os.path.join(project_root, "title_url_desc.csv")



@advanced_search_bp.route('/advanced_search', methods=['GET', 'POST'])
def advanced_search():
    
    # 检查用户是否已登录
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

   
    search_history_records = SearchHistory.query.filter_by(user_id=user_id).order_by(SearchHistory.timestamp.desc()).limit(12).all()
    search_history = [record.keyword for record in search_history_records]
    results = []

    if request.method == 'POST':
        # 从前端接收表单数据
        keywords = request.form.get('all_these_words', '').strip()
        #exact_phrase = request.form.get('exact_phrase', '').strip()
        site_or_domain = request.form.get('site_or_domain', '').strip()
        is_title_only = False
        
        # 解析短语查询字段
        exact_phrases_raw = request.form.get('exact_phrase', '')
        exact_phrases = [phrase.strip() for phrase in re.split(r'[;,]', exact_phrases_raw) if phrase.strip()]

        # 判断是否启用通配符查询
        enable_wildcard = request.form.get('enable_wildcard', False)
        enable_wildcard = enable_wildcard == 'true'  # 只有选中时才为 True

        t = time.perf_counter()  # 计时
        try:
            # 调用高级搜索逻辑
            current_app.logger.debug("Calling main function with keywords: %s, history: %s, is_title_only: %s", keywords, search_history, is_title_only)
            
            result_list = main_func(
                input_word=keywords,
                history_words=search_history,
                is_title_only=is_title_only,
                exact_phrases=exact_phrases,
                site_domain=site_or_domain,
                enable_wildcard=enable_wildcard  # 传递启用通配符的标志
            )
            current_app.logger.debug("Search results received: %s", result_list)
            

            current_app.logger.info("Search results: %s", result_list)

            url_title_desc = pd.read_csv(csv_path, encoding='utf-8-sig', index_col='url')
            

            for url, similarity in result_list:
                if url not in url_title_desc.index:
                    current_app.logger.warning("URL %s not found in title_url_desc index.", url)
                    continue  # 跳过索引中未找到的 URL
                
                # 从索引中获取标题和描述
                temp_series = url_title_desc.loc[url].fillna('')
                title = temp_series['title'].replace('_', '/') if 'title' in temp_series else "Unknown Title"
                description = temp_series['description'] if 'description' in temp_series else "No Description"
                page_rank_score = page_rank_df.loc[url]['page_rank'] if url in page_rank_df.index else 1.0
                weighted_score = similarity * page_rank_score
                results.append((title, url, description, weighted_score))

            # 按加权得分排序
            results.sort(key=lambda x: x[3], reverse=True)

        except Exception as e:
            current_app.logger.error("Error occurred during search: %s", str(e))
            results = []
        
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
    return render_template('advanced_search.html', search_history=search_history)  # if request.method == 'GET' and request.args.get('keywords'):
   