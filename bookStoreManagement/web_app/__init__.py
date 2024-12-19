from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager

app = Flask('Trang bán sách trực tuyến')
app.secret_key = b'\x01\xfe\xc6h\xf8\xfc\xef6\xfe\xb8\xa0n\xc8\xcdI\xdb'
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "mysql+pymysql://root:%s@localhost/bookstore?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app=app)

login = LoginManager(app=app)
