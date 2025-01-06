# BookStoreManagement
Quản lý cửa hàng bán sách.

## Setup
- Hãy thêm các key ở `key.py`
- Thêm MAIL_USERNAME và MAIL_PASSWORD ở `__init__.py`

## Database
```python
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "mysql+pymysql://root:%s@localhost/bookstore?charset=utf8mb4" % quote('your_password')
```

