from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField

from models import *
from wtforms import PasswordField, FileField
from flask_login import current_user
from flask import redirect
from sqlalchemy.orm import configure_mappers
import utils
from flask_admin.form import Select2Widget


class MyAdmin(AdminIndexView):
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        # getattr(x, 'y', default) == x.y   Nếu x không tồn tại thuộc tính y thì trả về default
        return (getattr(current_user, 'role', None) == StaffRole.ADMIN or
                (getattr(current_user, 'active', False) and getattr(current_user, 'is_warehouse_staff', False)))

    def inaccessible_callback(self, name, **kwargs):  # Xử lý khi is_accessible() == False
        if current_user.is_anonymous:
            return redirect('/login?next=/admin')
        return self.render('admin/403.html', another='hoặc nhân viên kho')

    @expose('/')
    def index(self):
        return self.render('admin/index.html')


admin = Admin(app=app, name='Trang quản trị cửa hàng sách', template_mode='bootstrap4', index_view=MyAdmin())


class AdminPermissionModelView(ModelView):
    column_type_formatters = utils.MY_DEFAULT_FORMATTERS

    def is_accessible(self):
        return getattr(current_user, 'role', None) == StaffRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):  # Xử lý khi is_accessible() == False
        if current_user.is_anonymous:
            return redirect('/login?next=/admin')
        return self.render('admin/403.html')


class ManagerPermissionView(AdminPermissionModelView):

    def is_accessible(self):
        return (getattr(current_user, 'role', None) == StaffRole.ADMIN or
                (getattr(current_user, 'active', False) and getattr(current_user, 'is_warehouse_staff', False)))

    def inaccessible_callback(self, name, **kwargs):  # Xử lý khi is_accessible() == False
        if current_user.is_anonymous:
            return redirect('/login?next=/admin', )
        return self.render('admin/403.html', another='hoặc nhân viên kho')


class CustomerView(AdminPermissionModelView):
    # custom trường password phải đuơc che dấu
    form_overrides = {
        'password': PasswordField
    }
    column_exclude_list = ('password', 'address', 'avatar', 'created_date')
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


class BookView(ManagerPermissionView):
    column_list = ['title', 'original_price', 'quantity', 'active', 'average_star', 'authors']
    column_filters = ['title', 'original_price', 'average_star', 'authors.name']
    column_formatters = {
        'authors': lambda view, context, model, name: ', '.join([author.name for author in model.authors])
    }
    column_labels = {
        'title': 'Tên sản phẩm',
        'original_price': 'Giá gốc',
        'quantity': 'Số lượng',
        'active': 'Đang kinh doanh',
        'average_star': 'Điểm đánh giá (5)',
        'authors': 'Các tác giả',
        'exist_authors': 'Thêm tác giả'
    }
    column_editable_list = ['title', 'original_price', 'quantity', 'active']
    inline_models = [(Image, dict(form_overrides={'image': FileField},
                                  )),
                     Author,
                     ]
    form_excluded_columns = ['order_details', 'comments']
    column_searchable_list = ['title', 'authors.name']

    def search_placeholder(self):
        return "Tìm kiếm theo tên hoặc tác giả..."


admin.add_view(CustomerView(Customer, db.session))
admin.add_view(StaffView(Staff, db.session))
configure_mappers()
admin.add_view(BookView(Book, db.session))
admin.add_view(ModelView(Author, db.session))

