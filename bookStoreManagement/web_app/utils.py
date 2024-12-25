import cloudinary.uploader
from flask_login import current_user
from web_app import app
from flask_admin.model import typefmt
from sqlalchemy import DateTime


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
MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)

# Cập nhật formatter cho kiểu bool và các formatter khác
MY_DEFAULT_FORMATTERS.update({
    bool: bool_format,  # Định dạng bool thành V hoặc X
    # định dạng ngày tháng theo dd-mm-yyyy hour-minute-second
    DateTime: lambda view, context, value: value.strftime('%d-%m-%Y %H:%M:%S'),

})

