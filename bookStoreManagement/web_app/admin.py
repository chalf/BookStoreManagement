from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from models import *
from wtforms import PasswordField, FileField, IntegerField
from flask_login import current_user
from flask import redirect, flash
from sqlalchemy.orm import configure_mappers
import utils
from wtforms.validators import NumberRange
import cloudinary.uploader


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
    can_view_details = True

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
        'password': PasswordField  # khi cập nhật sẽ không hiện mật khẩu, bắt nhập mk mới
    }
    column_exclude_list = ('password', 'address', 'avatar', 'created_date')
    can_view_details = True
    can_edit = False

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
    can_delete = False
    column_list = ['isbn', 'title', 'original_price', 'quantity', 'active', 'average_star', 'authors']
    column_filters = ['title', 'original_price', 'average_star', 'authors.name']
    column_labels = {
        'title': 'Tên sản phẩm',
        'description': 'Mô tả',
        'original_price': 'Giá gốc',
        'quantity': 'Số lượng hàng tồn',
        'active': 'Đang kinh doanh',
        'average_star': 'Điểm đánh giá (5)',
        'authors': 'Các tác giả',
        'writers': 'Thêm tác giả'
    }
    column_editable_list = ['title', 'original_price', 'active']
    inline_models = [(Image, dict(form_overrides={'image': FileField},
                                  )),
                     Author,
                     ]
    form_columns = ['isbn', 'title', 'description', 'original_price', 'quantity', 'imported_quantity',
                    'active', 'categories', 'images', 'authors', 'writers']
    form_widget_args = {
        'quantity': {
            'readonly': True
        }
    }
    form_extra_fields = {
        'imported_quantity': IntegerField(label='Số lượng nhập hàng', validators=[
            NumberRange(min=0, max=utils.read_config_json().get('MAX_QUANTITY'))], default=0)
    }
    form_args = {
        'authors': {
            'get_label': 'name'  # Sử dụng thuộc tính name làm nhãn
        },
    }
    column_searchable_list = ['title', 'authors.name']

    def search_placeholder(self):
        return "Tìm kiếm theo tên hoặc tác giả..."

    _regulations = utils.read_config_json()

    def _check_quantity_limits(self, form, model, is_created):
        # Đang Cập nhật và trường imported_quantity có thay đổi (khác 0) (tức là có cập nhật trường imported_quantity)
        # và model.quantity < số hàng tồn được phép nhập hàng
        if not is_created and form.imported_quantity.data \
                and model.quantity >= self._regulations.get('LIMIT_EDIT_QUANTITY'):
            return False
        return True

    # Hàm này được gọi khi cập nhật (Edit tab)
    def update_model(self, form, model):
        if not self._check_quantity_limits(form, model, False):
            flash(
                f'Số lượng hàng tồn phải ít hơn {self._regulations.get('LIMIT_EDIT_QUANTITY')} mới được nhập thêm hàng',
                'error')
            return False

        return super().update_model(form, model)

    def on_model_change(self, form, model, is_created):
        model.quantity += form.imported_quantity.data
        # upload images
        if form.images.data and model.images:
            book_images = form.images.data
            for book_image, image_property in zip(book_images, model.images):
                # book_image của book_images; image_property của model.images; zip() giúp loop trên 2 iterable cùng lúc
                url = cloudinary.uploader.upload(book_image.get('image')).get('secure_url')
                image_property.image = url


admin.add_view(CustomerView(Customer, db.session))
admin.add_view(StaffView(Staff, db.session))
admin.add_view(ModelView(Author, db.session))
configure_mappers()
admin.add_view(BookView(Book, db.session))
