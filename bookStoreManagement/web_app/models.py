from web_app import app, db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Time
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from enum import Enum as StatusAndType


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)


class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    original_price = Column(Integer, default=0)
    quantity = Column(Integer, default=1)
    active = Column(Boolean, default=True)    #True: còn hàng
    images = relationship('Image', backref='book', lazy='joined')
    categories = relationship(Category, secondary='category_product', lazy='joined',
                              backref=backref('books', lazy=True))
    order_details = relationship('OrderDetail', backref='book')


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
    price_reduction = Column(Integer, default=0)    #Số tiền giảm
    order_details = relationship('OrderDetail', backref='order')
    sales_agent = Column(Integer, ForeignKey('staff.id'), nullable=True)
    #nullable=True là để quan hệ many-to-one khi Staff xóa thì khóa ngoại sẽ SET NULL


class OrderDetail(db.Model):
    order_id = Column(ForeignKey(Order.id), primary_key=True)
    book_id = Column(ForeignKey(Book.id), primary_key=True)
    price = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)


class UserInfo(db.Model):
    __abstract__ = True

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
    avatar = Column(String(150), nullable=False)


class StaffRole(StatusAndType):
    SALES_AGENT = 1
    SECURITY_GUARD = 2


class Staff(UserInfo):
    starting_date = Column(DateTime, nullable=True)
    ending_date = Column(DateTime, nullable=True)
    role = Column(Enum(StaffRole), nullable=True)
    active = Column(Boolean, default=True)
    orders = relationship(Order, backref='sales_agent', lazy=True)


class Shift(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    staffs = relationship(Staff, secondary='shift_worker', lazy='subquery', backref='shift')


shift_worker = db.Table('shift_worker',
                        Column('staff_id', Integer, ForeignKey(Staff.id), primary_key=True),
                        Column('shift_id', Integer, ForeignKey(Shift.id), primary_key=True))


class CustomerType(StatusAndType):
    REGULAR = 1
    LOYAL = 2


class Customer(UserInfo):
    type = Column(Enum(CustomerType), default=CustomerType.REGULAR)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
