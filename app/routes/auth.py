from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.register'))

        # 创建新用户
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 验证用户
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username

            flash('登录成功', 'success')
            return redirect(url_for('front.index'))  # 登录后跳转到主页
        flash('用户名或密码错误', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """
    用户注销
    """
    session.clear()
    flash('您已成功退出', 'success')
    return redirect(url_for('auth.login'))
