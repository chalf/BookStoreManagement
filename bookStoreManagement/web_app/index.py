import json
import math
import utils
from web_app import app, login
from flask import render_template, redirect, request, jsonify, make_response, flash, url_for, session
import dao
from flask_login import login_user, logout_user, current_user, login_required
from models import CustomerType, OrderStatus


@app.context_processor
def common_response():
    cart_key = utils.get_cart_key()
    return {
        'categories': dao.get_categories(),
        'cart_stats': utils.stats_cart(session.get(cart_key))
    }


@app.route('/')
def index():
    pictures = [url_for('static', filename=f'image/index/{i}.png') for i in range(1, 6)]

    books = dao.get_books(kw=request.args.get('keyword'), page_number=int(request.args.get('page', 1)),
                          cate_id=request.args.get('category_id'))
    page_size = app.config['PAGE_SIZE']
    num_of_books = dao.count_books()
    return render_template('index.html', pictures=pictures, books=books,
                           num_of_books=math.ceil(num_of_books / page_size))


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
            utils.merge_cart()
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


@app.template_filter('order_status')
def customer_type_filter(status):
    if status == OrderStatus.ORDERED:
        return 'Chưa lấy hàng'
    if status == OrderStatus.PAID or status == OrderStatus.RECEIVED:
        return 'Hoàn thành'
    if status == OrderStatus.CANCELED:
        return 'Đã hủy'


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
    else:  # nếu là request chỉnh sửa thông tin
        data = request.form
        dao.update_user(data)
        return redirect('/user/details')


@app.route('/cart/')
def get_cart():
    return render_template('cart.html', cart_key=utils.get_cart_key())


@app.route('/api/carts/', methods=['POST'])
def add_to_cart():
    """
    session['cart']: {
        "1": {
            "id": "1",
            "title": "abc",
            "price": 123,
            "image": image1.png
            "purchase_quantity": 1
        }, "2": {
            "id": "2",
            "title": "abc",
            "price": 123,
            "image": image2.png,
            "purchase_quantity": 1
        }
    }
    """
    cart_key = utils.get_cart_key()
    cart = session.get(cart_key, {})

    id = str(request.json.get('id'))
    title = request.json.get('title')
    price = request.json.get('price')
    image = request.json.get('image')

    if id in cart:
        cart[id]['purchase_quantity'] += 1
    else:
        cart[id] = {
            'id': id,
            'title': title,
            'price': price,
            'image': image,
            'purchase_quantity': 1
        }

    session[cart_key] = cart
    return jsonify(utils.stats_cart(cart))


@app.route('/api/carts/<book_id>', methods=['PUT'])
def update_cart(book_id):
    cart_key = utils.get_cart_key()
    cart = session.get(cart_key)
    if cart and book_id in cart:
        quantity = int(request.json.get('quantity', 0))
        cart[book_id]['purchase_quantity'] = quantity
        session[cart_key] = cart
    return jsonify(utils.stats_cart(cart))


@app.route('/api/carts/<book_id>', methods=['DELETE'])
def delete_cart(book_id):
    card_key = utils.get_cart_key()
    cart = session.get(card_key)
    if cart and book_id in cart:
        del cart[book_id]
        session[card_key] = cart

    return jsonify(utils.stats_cart(cart))


@app.route('/payments/')
def one_step_before_pay():
    import key
    cart_key = utils.get_cart_key()

    # Kiểm tra số lượng hàng trong kho
    is_valid, message = dao.check_quantity(cart_key)
    if not is_valid:
        return render_template('cart.html', error=message)

    if request.args.get('paymentMethod').__eq__('paypal'):
        cart_stats = utils.stats_cart(session.get(utils.get_cart_key()))
        usd = utils.convert_VND_to_USD(cart_stats['total_amount'])
        return render_template('payment_by_paypal.html', client_id=key.PAYPAL_BUSINESS_CLIENT_ID,
                               currency=key.IB_TAX_APP_PRICE_CURRENCY, total_amount=usd)

    elif request.args.get('paymentMethod').__eq__('store'):
        cart_key = utils.get_cart_key()
        cart = session.get(cart_key)
        dao.create_order(cart=cart, is_online_payment=False)
        session[cart_key] = {}  # Đặt thành công thì clean giỏ
        return render_template('payment_at_store.html')
    return '<h1>404 - Not Found</h1>'


@app.route("/payments/<order_id>/capture", methods=["POST"])
def capture_payment(order_id):  # Checks and confirms payment
    captured_payment = utils.approve_payment(order_id)
    # print(captured_payment) # or you can do some checks from this captured data details
    if captured_payment.get('status').__eq__('COMPLETED'):
        cart_key = utils.get_cart_key()
        cart = session.get(cart_key)
        dao.create_order(cart=cart, is_online_payment=True)
        session[cart_key] = {}  # Thanh toán thành công thì clean giỏ
    return jsonify(captured_payment)


@app.route('/sales/')
def sale_book():
    # Thỏa mãn TẤT CẢ 3 điều kiện mới vào được:
    # 1. Phải đăng nhập
    # 2. Phải là nhân viên
    # 3. Phải là nhân viên bán hàng hoặc là ADMIN
    if (not current_user.is_authenticated or not current_user.is_staff() or
            (not current_user.is_sale_agent() and not current_user.is_admin())):
        return '<h1>403 - Forbidden</h1>'

    kw = request.args.get('kw-at-sale-page')
    books = dao.get_books(kw=kw)
    data = utils.stats_cart(session.get('order'))
    return render_template('book_seller.html', books=books, data=json.dumps(data))


@app.route('/api/sale-book', methods=['POST'])
def create_order_at_sale_page():
    """
        session['order']: {
            "1": {
                "id": 1
                "isbn": "1",
                "title": "abc",
                "price": 123,
                "purchase_quantity": 1
            }, "2": {
                "id": "2",
                "isbn": "442121",
                "title": "abc",
                "price": 123,
                "purchase_quantity": 1
            }
        }
        """
    cart = session.get('order')
    if not cart:
        cart = {}
    id = str(request.json.get('id'))
    isbn = request.json.get('isbn')
    name = request.json.get('name')
    price = request.json.get('price')

    if id not in cart:
        cart[id] = {
            'id': id,
            'isbn': isbn,
            'name': name,
            'price': price,
            'purchase_quantity': 1
        }

    session['order'] = cart
    data = utils.stats_cart(cart)
    return jsonify(data)


@app.route('/api/sale-book/<book_id>', methods=['PUT'])
def update_order_at_sale_page(book_id):
    cart = session.get('order')
    if cart and book_id in cart:
        quantity = int(request.json.get('quantity', 0))
        cart[book_id]['purchase_quantity'] = quantity
        session['order'] = cart
    return jsonify(utils.stats_cart(cart))


@app.route('/api/sale-book/<book_id>', methods=['DELETE'])
def delete_order_at_sale_page(book_id):
    cart = session.get('order')
    if cart and book_id in cart:
        del cart[book_id]
        session['order'] = cart

    return jsonify(utils.stats_cart(cart))


@app.route('/api/orders/', methods=['POST'])
def create_order():
    order = dao.create_order_case_selling_at_store(cart=session.get('order'))
    session['order'] = {}
    return jsonify({'status': 201})


@app.route('/api/get-orders/')
def user_orders_process():
    status = request.args.get('status')
    rs = dao.get_order_of_user(status)
    return jsonify(rs)
    # return render_template('my_order.html', orders=rs)


@app.route('/user/my-order/')
@login_required
def user_orders():
    return render_template('my_order.html')


@app.route('/test/')
def test():
    return jsonify({'id': '6VB599845B828553W', 'status': 'COMPLETED', 'payment_source': {
        'paypal': {'email_address': 'hieudtn3@gmail.com', 'account_id': 'SBAJDUJC74RRY', 'account_status': 'UNVERIFIED',
                   'name': {'given_name': 'Test', 'surname': 'Ting'}, 'address': {'country_code': 'VN'}}},
                    'purchase_units': [{'reference_id': 'default', 'shipping': {'name': {'full_name': 'Test Ting'},
                                                                                'address': {
                                                                                    'address_line_1': 'Nguyen Trai',
                                                                                    'admin_area_2': 'QUan 5',
                                                                                    'admin_area_1': 'HỒ CHÍ MINH',
                                                                                    'country_code': 'VN'}},
                                        'payments': {'captures': [{'id': '91F01807J3540224W', 'status': 'COMPLETED',
                                                                   'amount': {'currency_code': 'USD', 'value': '0.20'},
                                                                   'final_capture': True,
                                                                   'seller_protection': {'status': 'ELIGIBLE',
                                                                                         'dispute_categories': [
                                                                                             'ITEM_NOT_RECEIVED',
                                                                                             'UNAUTHORIZED_TRANSACTION']},
                                                                   'seller_receivable_breakdown': {
                                                                       'gross_amount': {'currency_code': 'USD',
                                                                                        'value': '0.20'},
                                                                       'paypal_fee': {'currency_code': 'USD',
                                                                                      'value': '0.20'},
                                                                       'net_amount': {'currency_code': 'USD',
                                                                                      'value': '0.00'}}, 'links': [{
                                                                                                                       'href': 'https://api.sandbox.paypal.com/v2/payments/captures/91F01807J3540224W',
                                                                                                                       'rel': 'self',
                                                                                                                       'method': 'GET'},
                                                                                                                   {
                                                                                                                       'href': 'https://api.sandbox.paypal.com/v2/payments/captures/91F01807J3540224W/refund',
                                                                                                                       'rel': 'refund',
                                                                                                                       'method': 'POST'},
                                                                                                                   {
                                                                                                                       'href': 'https://api.sandbox.paypal.com/v2/checkout/orders/6VB599845B828553W',
                                                                                                                       'rel': 'up',
                                                                                                                       'method': 'GET'}],
                                                                   'create_time': '2024-12-30T14:53:16Z',
                                                                   'update_time': '2024-12-30T14:53:16Z'}]}}],
                    'payer': {'name': {'given_name': 'Test', 'surname': 'Ting'}, 'email_address': 'hieudtn3@gmail.com',
                              'payer_id': 'SBAJDUJC74RRY', 'address': {'country_code': 'VN'}}, 'links': [
            {'href': 'https://api.sandbox.paypal.com/v2/checkout/orders/6VB599845B828553W', 'rel': 'self',
             'method': 'GET'}]})


if __name__ == '__main__':
    from admin import admin

    app.run(debug=True, port=2357)
