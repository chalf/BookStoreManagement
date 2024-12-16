from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import *

admin = Admin(app=app, name='Trang quản trị cửa hàng sách', template_mode='bootstrap4')

admin.add_view(ModelView(Book, db.session))
