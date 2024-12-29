from models import *
import datetime
from flask_login import current_user
import cloudinary.uploader
import cloudinary.api
import utils
from sqlalchemy import or_


#     -------------------    USER    -----------------------
def get_user_by_id(id):
    # one_or_none() tức là nếu có đúng 1 record thì trả về, nếu nhiều hơn thì lỗi
    # nếu không có record nào thì None, nếu None thì truy vấn Customer
    return db.session.query(Staff).filter(Staff.id == id).one_or_none() or \
        Customer.query.get(id)


def get_user_by_username(name):
    return db.session.query(Staff).filter(Staff.username == name).one_or_none() or \
        Customer.query.filter_by(username=name).first()


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = Customer.query.filter(Customer.username.__eq__(username), Customer.password.__eq__(password))
    # filter() trả về query
    return user.first()


def update_last_login_date(user):
    user.last_login_date = datetime.datetime.now()
    db.session.add(user)
    db.session.commit()


def create_user(username, password, phone_number, first_name, last_name, email=None, address=None):
    existing_user = get_user_by_username(username)
    if existing_user:
        return None
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    customer = Customer(username=username, password=password, phone_number=phone_number, first_name=first_name,
                        last_name=last_name, email=email, address=address)
    db.session.add(customer)
    db.session.commit()
    return get_user_by_id(customer.id)


def update_user(data):
    current_user.first_name = data.get('first_name')
    current_user.last_name = data.get('last_name')
    current_user.email = data.get('email')
    current_user.phone_number = data.get('phone_number')
    db.session.add(current_user)
    db.session.commit()


def update_user_avatar(file):
    upload_result = cloudinary.uploader.upload(file)
    if not utils.is_default_avatar():
        public_id = utils.get_public_id(current_user.avatar)
        utils.delete_img(public_id)
    current_user.avatar = upload_result['secure_url']
    db.session.add(current_user)
    db.session.commit()


#     -------------------    PRODUCT    -----------------------
def get_books(cate_id=None, kw=None, page_number=1):
    books = Book.query
    if cate_id:
        books = (books.join(category_product, Book.id == category_product.c.book_id)
                 .filter(category_product.c.category_id == cate_id))
    if kw:
        books = books.join(author_book, Book.id == author_book.c.book_id, isouter=True)\
                     .join(Author, author_book.c.author_id == Author.id, isouter=True)\
                     .filter(or_(Book.title.icontains(kw), Author.name.icontains(kw)))\
                     .distinct()

    page_size = app.config['PAGE_SIZE']
    start = (page_number - 1) * page_size
    books = books.slice(start, start + page_size)

    return books.all()


def count_books():
    return Book.query.count()


#     -------------------    PRODUCT    -----------------------
def get_categories():
    return Category.query.all()


if __name__ == '__main__':
    with app.app_context():
        print(get_user_by_username('0gg'))
