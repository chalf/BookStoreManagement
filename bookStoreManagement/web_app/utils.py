import cloudinary.uploader
from flask_login import current_user
from web_app import app


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
