from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary

app = Flask('Trang bán sách trực tuyến')
app.secret_key = b'\x01\xfe\xc6h\xf8\xfc\xef6\xfe\xb8\xa0n\xc8\xcdI\xdb'

app.config['DEFAULT_PUBLIC_ID'] = 'default_avatar_ovzdky'
app.config['PAGE_SIZE'] = 3

# Cấu hình Database
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "mysql+pymysql://root:%s@localhost/bookstore?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app=app)

# Cấu hình Cloudinary
cloudinary.config(
    cloud_name="dtufi97qw",
    api_key="415675355348994",
    api_secret="LJ6gCnEZUfFk3zU6OfbNb0b6jrQ",
    secure=True
)

# Flask Login object
login = LoginManager(app=app)


# Cấu hình sửa lỗi CORS policy
@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response
