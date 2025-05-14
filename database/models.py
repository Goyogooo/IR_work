from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from app import db  # 导入db实例

# 用户表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  # 用户 ID
    username = db.Column(db.String(80), unique=True, nullable=False)  # 用户名
    password = db.Column(db.String(200), nullable=False)  # 密码
    search_history = db.relationship('SearchHistory', backref='user', lazy=True)  # 关联搜索历史


class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    id = db.Column(db.Integer, primary_key=True)  # 历史记录ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    keyword = db.Column(db.String(200), nullable=False)  # 搜索关键词
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 搜索时间

class UserSnapshot(db.Model):
    __tablename__ = 'user_snapshots'
    id = db.Column(db.Integer, primary_key=True)  # 记录ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 用户ID
    url = db.Column(db.String(500), nullable=False)  # 快照的URL
    title = db.Column(db.String(200), nullable=False)  # 快照的标题
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 快照保存时间

    user = db.relationship('User', backref='snapshots')  # 关联到用户
