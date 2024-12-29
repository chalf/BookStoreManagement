import cloudinary.uploader
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from web_app import app
from flask_admin.contrib.sqla import typefmt
from sqlalchemy import DateTime
import json
import os


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


# Sao chép formatter mặc định
MY_DEFAULT_FORMATTERS = dict(typefmt.DEFAULT_FORMATTERS)

# Cập nhật formatter cho kiểu bool và các formatter khác
MY_DEFAULT_FORMATTERS.update({
    bool: bool_format,  # Định dạng bool thành V hoặc X
    # định dạng ngày tháng theo dd-mm-yyyy hour-minute-second
    DateTime: lambda view, context, value: value.strftime('%d-%m-%Y %H:%M:%S'),

})


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


if __name__ == '__main__':
    # print(read_config_json())
    # write_config_json(150, 300)
    # print(read_config_json())
    a = FileStorage
    for key, formatter in MY_DEFAULT_FORMATTERS.items():
        print(f"Key: {key}, Formatter: {formatter}")

