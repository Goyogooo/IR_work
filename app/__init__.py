from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'ir'  # 根据实际配置
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'my_super_secret_key'

    # 初始化数据库
    db.init_app(app)

     # 配置日志记录器
    configure_logging(app)

    # 测试数据库连接
    with app.app_context():
        try:
            db.engine.connect()  # 尝试连接数据库
            print("数据库连接成功！")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            
    # 在此处注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.index import front
    from app.routes.search_routes import search_bp
    from app.routes.advanced_search_routes import advanced_search_bp
    from app.routes.snapshot import snapshot_bp
    from app.routes.download import file_download_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(front, url_prefix='/')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(advanced_search_bp, url_prefix='/advanced')
    app.register_blueprint(snapshot_bp, url_prefix='/snapshots')
    app.register_blueprint(file_download_bp, url_prefix='/files')
    
    return app

def configure_logging(app):
    """
    配置日志记录器
    """
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建日志处理器（输出到文件）
    file_handler = logging.FileHandler('app.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # 创建日志处理器（输出到控制台）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # 将处理器添加到 Flask 的默认日志记录器
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    # 设置全局日志级别
    app.logger.setLevel(logging.DEBUG)