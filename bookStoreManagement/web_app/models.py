from web_app import app, db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Time, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from enum import Enum as StatusAndType
from flask_login import UserMixin
import hashlib


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)


class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    original_price = Column(Integer, default=0)
    quantity = Column(Integer, default=1)
    active = Column(Boolean, default=True)  # True: còn hàng
    average_star = Column(Float, default=0)
    images = relationship('Image', backref='book', lazy='joined')
    categories = relationship(Category, secondary='cate_prod', lazy='joined',
                              backref=backref('books', lazy=True))
    order_details = relationship('OrderDetail', backref='book')
    comments = relationship('Comment', backref='book')


class Image(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String(100), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)


category_product = db.Table('cate_prod',
                            Column('category_id', Integer, ForeignKey(Category.id), primary_key=True),
                            Column('book_id', Integer, ForeignKey(Book.id), primary_key=True))


class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship(Book, secondary='author_book', lazy='subquery',
                         backref=backref('authors', lazy='joined'))


author_book = db.Table('author_book',
                       Column('author_id', Integer, ForeignKey(Author.id), primary_key=True),
                       Column('book_id', Integer, ForeignKey(Book.id), primary_key=True))


class OrderStatus(StatusAndType):
    ORDERED = 1,
    PAID = 2
    CANCELED = 3
    RECEIVED = 4


class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=func.now())
    status = Column(Enum(OrderStatus), default=OrderStatus.ORDERED)
    price_reduction = Column(Integer, default=0)  # Số tiền giảm
    order_details = relationship('OrderDetail', backref='order')
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    # nullable=True là để quan hệ many-to-one khi Staff xóa thì khóa ngoại sẽ SET NULL
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)


class OrderDetail(db.Model):
    order_id = Column(ForeignKey(Order.id), primary_key=True)
    book_id = Column(ForeignKey(Book.id), primary_key=True)
    price = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)


class CustomerType(StatusAndType):
    REGULAR = 1
    LOYAL = 2


class Customer(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    phone_number = Column(String(15), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    created_date = Column(DateTime, default=func.now())
    last_login_date = Column(DateTime, default=func.now())
    avatar = Column(String(150),
                    default='https://res.cloudinary.com/dtufi97qw/image/upload/v1734447269/default_avatar_ovzdky.jpg')
    type = Column(Enum(CustomerType), default=CustomerType.REGULAR)
    orders = relationship(Order, backref='customer', lazy=True)
    comments = relationship('Comment', backref='customer')
    customer_owns_voucher = relationship('CustomerOwnsVoucher', backref='customer')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'avatar': self.avatar
        }


class StaffRole(StatusAndType):
    SALES_AGENT = 1
    SECURITY_GUARD = 2
    ADMIN = 3


class Staff(Customer):
    id = Column(Integer, ForeignKey(Customer.id, ondelete='CASCADE'), primary_key=True)
    starting_date = Column(DateTime, nullable=True)
    ending_date = Column(DateTime, nullable=True)
    role = Column(Enum(StaffRole), default=StaffRole.SALES_AGENT)
    active = Column(Boolean, default=True)
    agent_orders = relationship(Order, backref='sales_agent', lazy=True)


class Shift(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    staffs = relationship(Staff, secondary='shift_worker', lazy='subquery', backref='shift')


shift_worker = db.Table('shift_worker',
                        Column('staff_id', Integer, ForeignKey(Staff.id), primary_key=True),
                        Column('shift_id', Integer, ForeignKey(Shift.id), primary_key=True))


class Comment(db.Model):
    customer_id = Column(ForeignKey(Customer.id), primary_key=True)
    book_id = Column(ForeignKey(Book.id), primary_key=True)
    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())
    content = Column(String(255), nullable=True)
    star = Column(Integer, default=5)


class VoucherType(StatusAndType):
    FIXED_AMOUNT = 1  # Tiền cố định
    PERCENTAGE_DISCOUNT = 2  # Giảm theo phần trăm


class TermCondition:
    def is_satisfied(self, context: dict) -> bool:
        """
        Kiểm tra xem điều kiện có thỏa mãn không.
        :param context: Bối cảnh (dữ liệu đầu vào) cần để kiểm tra điều kiện.
        :return: True nếu điều kiện thỏa mãn, False nếu không.
        """
        pass


class Voucher(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)
    expiry = Column(DateTime, nullable=True)  # Ngày hết hạn
    voucher_type = Column(Enum(VoucherType), nullable=False)
    value = Column(Integer, nullable=False)  # Giá trị giảm giá (tiền hoặc %)
    max_value = Column(Integer, nullable=True)  # Số tiền giảm giá tối đa (nếu áp dụng type PERCENTAGE_DISCOUNT)
    condition_description = Column(String(255), nullable=True)
    condition = TermCondition()  # Điều kiện áp dụng voucher (nếu cần)
    customer_owns_voucher = relationship('CustomerOwnsVoucher', backref='voucher')


class CustomerOwnsVoucher(db.Model):
    customer_id = Column(ForeignKey(Customer.id), primary_key=True)
    voucher_id = Column(ForeignKey(Voucher.id), primary_key=True)
    quantity = Column(Integer, default=1)


if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        # staff = Staff(username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        #           first_name='Hieu', last_name='Duong', phone_number='0999999', role=StaffRole.ADMIN)
        # db.session.add(staff)
        # db.session.commit()
        ad = db.session.get(Staff, 7)
        print(ad.agent_orders)
