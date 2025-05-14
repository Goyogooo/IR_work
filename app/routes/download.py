from flask import Flask, send_from_directory, abort
from flask import Blueprint
import os

app = Flask(__name__)

# 获取当前脚本文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 项目根目录（两级上层：从 routes/search_routes.py 到 project 根目录）
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 定位 title_url_desc.csv 的路径
csv_path = os.path.join(project_root, "title_url_desc.csv")


# 文件存放路径
DOWNLOAD_FOLDER = os.path.join(project_root, "downloads")

# 确保这个目录存在
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 创建蓝图
file_download_bp = Blueprint('file_download', __name__)

@file_download_bp.route('/download/<filename>')
def download_file(filename):
    try:
        # 使用 Flask 的 send_from_directory 函数返回文件
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)  # 如果文件未找到，返回 404 错误
