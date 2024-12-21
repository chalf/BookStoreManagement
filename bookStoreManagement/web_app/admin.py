from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import *
from wtforms import PasswordField

admin = Admin(app=app, name='Trang quản trị cửa hàng sách', template_mode='bootstrap4')


class CustomerView(ModelView):
    # custom trường password phải đuơc che dấu
    form_overrides = {
        'password': PasswordField
    }
    column_exclude_list = ('password', 'address', 'avatar', 'created_date')

    # định dạng ngày tháng theo dd-mm-yyyy hour-minute-second
    column_formatters = {
        'created_date': lambda view, context, model, name: model.created_date.strftime('%d-%m-%Y %H:%M:%S'),
        'last_login_date': lambda view, context, model, name: model.last_login_date.strftime('%d-%m-%Y %H:%M:%S'),
    }
    can_view_details = True

    # xử lý mã hóa trước khi lưu model
    def on_model_change(self, form, model, is_created):
        password = None
        if form.password.data:
            password = form.password.data.strip()
        if password:
            model.password = str(hashlib.md5(password.encode('utf-8')).hexdigest())


class StaffView(CustomerView):
    column_exclude_list = ('password', 'address', 'avatar', 'created_date', 'type')


admin.add_view(CustomerView(Customer, db.session))
admin.add_view(StaffView(Staff, db.session))
