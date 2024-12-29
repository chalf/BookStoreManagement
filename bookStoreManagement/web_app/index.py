import json
import math

from web_app import app, login
from flask import render_template, redirect, request, jsonify, make_response, flash, get_flashed_messages, url_for
import dao
from flask_login import login_user, logout_user, current_user, login_required
from models import CustomerType


@app.context_processor
def common_response():
    return {
        'categories': dao.get_categories(),
        # 'cart_stats': utils.stats_cart(session.get('cart'))
    }


@app.route('/')
def index():
    pictures = [url_for('static', filename=f'image/index/{i}.png') for i in range(1, 6)]

    books = dao.get_books(kw=request.args.get('keyword'), page_number=int(request.args.get('page', 1)),
                          cate_id=request.args.get('category_id'))
    page_size = app.config['PAGE_SIZE']
    num_of_books = dao.count_books()
    return render_template('index.html', pictures=pictures, books=books,
                           num_of_books=math.ceil(num_of_books/page_size))


@app.route('/login/', methods=['GET', 'POST'])
def login_process():
    # nếu đăng nhập rồi thì không hiện form đăng nhập nữa
    if current_user.is_authenticated:
        return redirect('/')
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            dao.update_last_login_date(user)
            next_url = request.args.get('next')
            return redirect(next_url) if next_url else redirect('/')
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')

    return render_template('login.html')


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/logout/')
def logout_user_process():
    next_url = request.args.get('next')
    logout_user()
    return redirect(next_url) if next_url else redirect('/login')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    # nếu đang đăng nhập thì không hiện form đăng ký
    if current_user.is_authenticated:
        return redirect('/')
    if request.method.__eq__('POST'):
        userinfo = request.form
        created_user = dao.create_user(**userinfo)
        if not created_user:
            flash('Tên đăng nhập này đã được sử dụng', 'warning')
        else:
            login_user(created_user)
            return redirect('/')
    return render_template('register.html')


@app.template_filter('customer_type')
def customer_type_filter(type):
    return 'Khách hàng thông thường' if type == CustomerType.REGULAR else 'Khách hàng thân thiết'


@app.route('/user/details/')
@login_required
def user_details():
    return render_template('personal_page.html')


@app.route('/api/user/edit/', methods=['POST'])
@login_required
def update_user():
    # nếu là request đổi avatar
    if request.files.get('avatar'):
        dao.update_user_avatar(request.files.get('avatar'))
        return make_response('', 200)
    else: # nếu là request chỉnh sửa thông tin
        data = request.form
        dao.update_user(data)
        return redirect('/user/details')


if __name__ == '__main__':
    from admin import admin
    app.run(debug=True, port=2357)
