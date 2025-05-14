import os
from flask import Blueprint, request, render_template, Markup, jsonify, session
from database.models import db, UserSnapshot

# 定义蓝图
snapshot_bp = Blueprint('snapshot', __name__)

# 快照展示
@snapshot_bp.route('/snapshot')
def _snapshot():
    """
    展示单个快照内容
    """
    url = request.args.get('url') 
    if not url or not isinstance(url, str):
        return "不合法的参数", 400

    # 模拟数据字典：从你的配置中获取URL到标题的映射
    url_title_df = {
        "https://example.com/page1": {"title": "Page 1"},
        "https://example.com/page2": {"title": "Page 2"}
    }

    # 检查 URL 是否存在
    if url not in url_title_df:
        return "快照不存在或参数错误", 404

    title = url_title_df[url]['title']

    # 获取项目根路径
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    snapshot_path = os.path.join(PROJECT_ROOT, 'page', f'{title}.html')

    # 检查快照文件是否存在
    if not os.path.exists(snapshot_path):
        return "快照文件不存在", 404

    try:
        with open(snapshot_path, encoding='utf-8') as f:
            snapshot = f.read()
    except Exception as e:
        return f"文件读取错误: {str(e)}", 500

    # 返回快照内容
    return render_template('snapshot.html', snapshot=Markup(snapshot))

# 我的快照
@snapshot_bp.route('/my_snapshots', methods=['GET'])
def my_snapshots():
    """
    展示用户保存的所有快照
    """
    user_id = session.get('user_id')  # 假设用户已登录，ID保存在 session 中
    if not user_id:
        return "用户未登录", 401

    # 查询用户的快照记录
    user_snapshots = UserSnapshot.query.filter_by(user_id=user_id).all()

    # 构造快照列表
    snapshots = [
        {"url": snapshot.url, "title": snapshot.title, "timestamp": snapshot.timestamp}
        for snapshot in user_snapshots
    ]

    return render_template('my_snapshots.html', snapshots=snapshots)

# 添加快照
@snapshot_bp.route('/add', methods=['POST'])
def add_snapshot():
    """
    保存用户选择的快照记录
    """
    user_id = session.get('user_id')  # 假设用户已登录，ID保存在 session 中
    if not user_id:
        return {"message": "用户未登录"}, 401

    url = request.form.get('url')
    title = request.form.get('title')

    if not url or not title:
        return {"message": "缺少必要参数"}, 400

    # 检查用户是否已保存该快照
    existing_snapshot = UserSnapshot.query.filter_by(user_id=user_id, url=url).first()
    if existing_snapshot:
        return {"message": "该快照已保存！"}, 400

    # 保存快照记录
    snapshot = UserSnapshot(user_id=user_id, url=url, title=title)
    db.session.add(snapshot)
    db.session.commit()

    return {"message": "快照已保存成功！"}
