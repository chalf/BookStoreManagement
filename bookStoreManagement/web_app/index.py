from web_app import app, login
from flask import render_template, redirect, request
import dao
from flask_login import login_user, logout_user, current_user


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/', methods=['GET', 'POST'])
def login_process():
    # nếu đăng nhập rồi thì không hiện form đăng nhập nữa
    if current_user.is_authenticated:
        return redirect('/')
    error = None
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            dao.update_last_login_date(user)
            return redirect('/')
        else:
            error = 'Tên đăng nhập hoặc mật khẩu không đúng!'

    return render_template('login.html', error=error)


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/logout/')
def logout_user_process():
    logout_user()
    return redirect('/login')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    # nếu đang đăng nhập thì không hiện form đăng ký
    if current_user.is_authenticated:
        return redirect('/')
    if request.method.__eq__('POST'):
        userinfo = request.form
        created_user = dao.create_user(**userinfo)
        login_user(created_user)
        return redirect('/')
    return render_template('register.html')


if __name__ == '__main__':
    from admin import admin
    app.run(debug=True, port=2357)
