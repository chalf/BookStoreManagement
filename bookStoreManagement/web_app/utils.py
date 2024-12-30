import cloudinary.uploader
from flask_login import current_user
from web_app import app
from flask_admin.contrib.sqla import typefmt
import json
import os
from datetime import datetime
from flask import session
from requests.auth import HTTPBasicAuth
import requests


# Lấy public_id từ url ảnh trên cloudinary
def get_public_id(secure_url):
    return secure_url.split('/')[-1].split('.')[0]


# Xóa ảnh trên cloudinary
def delete_img(public_id):
    response = cloudinary.uploader.destroy(public_id)
    return True if response['result'] == 'ok' else False


# Kiểm tra current_user có đang để avatar mặc định không
def is_default_avatar():
    public_id = get_public_id(current_user.avatar)
    return True if public_id.__eq__(app.config['DEFAULT_PUBLIC_ID']) else False


# Định nghĩa formatter cho kiểu bool
def bool_format(view, value):
    return '✔' if value else '✘'


def get_formatter():
    # Sao chép formatter mặc định
    MY_DEFAULT_FORMATTERS = dict(typefmt.DEFAULT_FORMATTERS)

    # Cập nhật formatter cho kiểu bool và các formatter khác
    MY_DEFAULT_FORMATTERS.update({
        bool: bool_format,  # Định dạng bool thành V hoặc X
        # định dạng ngày tháng theo dd-mm-yyyy hour-minute-second
        datetime: lambda view, value: value.strftime('%d-%m-%Y %H:%M:%S'),
    })
    return MY_DEFAULT_FORMATTERS


def read_config_json():
    """ Hàm này trả về dictionary """
    path = os.path.join(app.root_path, 'static/regulations.json')
    with open(path, 'r', encoding='utf-8') as f:
        y = json.loads(f.read())
        return y


def write_config_json(limit_edit_quantity, max_quantity):
    """
    :param limit_edit_quantity: số lượng tồn tối đa,
        VD: limit_edit_quantity là 150, thì ít hơn 150 mới được phép nhập thêm hàng
    :param max_quantity: số lượng tối đa được phép nhập
    """
    path = os.path.join(app.root_path, 'static/regulations.json')
    with open(path, 'w', encoding='utf-8') as f:
        config_data = {
            'LIMIT_EDIT_QUANTITY': limit_edit_quantity,
            'MAX_QUANTITY': max_quantity
        }
        f.write(json.dumps(config_data, indent=4))


def get_cart_key():
    cart_key = f'cart_{current_user.id}' if current_user.is_authenticated else 'guest_cart'
    return cart_key


def stats_cart(cart):
    # tổng số lượng và tổng tiền
    total_quantity, total_amount = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['purchase_quantity']
            total_amount += c['purchase_quantity'] * c['price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }


def merge_cart():
    try:
        guest_cart = session.pop('guest_cart')
    except KeyError:
        guest_cart = {}
    user_cart_key = f'cart_{current_user.id}'
    user_cart = session.get(user_cart_key, {})

    # Hợp nhất
    if guest_cart:
        for id, item in guest_cart.items():
            if id in user_cart:
                user_cart[id]['purchase_quantity'] += item['purchase_quantity']
            else:
                user_cart[id] = item

    session[user_cart_key] = user_cart


def approve_payment(order_id):
    import key
    api_link = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture'
    client_id = key.PAYPAL_BUSINESS_CLIENT_ID
    secret = key.PAYPAL_BUSINESS_SECRET
    basic_auth = HTTPBasicAuth(client_id, secret)
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url=api_link, headers=headers, auth=basic_auth)
    response.raise_for_status()
    json_data = response.json()
    return json_data


if __name__ == '__main__':
    dic = {
        '1': 11,
        True: ('p',)
    }

