from flask import session
from sqlalchemy.exc import NoResultFound
from models import *
import datetime
from flask_login import current_user
import cloudinary.uploader
import cloudinary.api
import utils
from sqlalchemy import or_, extract, func


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
    # validate username không được trùng lặp
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
def pagination(books, page_number):
    """ :param books: đối tượng query """
    page_size = app.config['PAGE_SIZE']
    start = (page_number - 1) * page_size
    books = books.slice(start, start + page_size)

    return books.all()


def get_books(cate_id=None, kw=None, page_number=1):
    books = Book.query.filter_by(active=True)
    if cate_id:
        books = (books.join(category_product, Book.id == category_product.c.book_id)
                 .filter(category_product.c.category_id == cate_id))
        return books.all()

    if kw:
        books = books.join(author_book, Book.id == author_book.c.book_id, isouter=True) \
            .join(Author, author_book.c.author_id == Author.id, isouter=True) \
            .filter(or_(Book.title.icontains(kw), Book.isbn.icontains(kw), Author.name.icontains(kw))) \
            .distinct()
        return books.all()

    return pagination(books, page_number)


def count_books():
    return Book.query.count()


def get_categories():
    return Category.query.all()


def check_quantity(cart_key):
    cart = session.get(cart_key, {})
    for item in cart.values():
        try:
            book = Book.query.filter_by(id=item['id']).one()
            if item['purchase_quantity'] > book.quantity:
                return False, f"Sản phẩm '{book.title}' chỉ còn {book.quantity} sản phẩm trong kho."
        except NoResultFound:
            return False, f"Sản phẩm với ID {item['id']} không tồn tại."
    return True, None


#     -------------------    ORDER    -----------------------
def create_order(cart, is_online_payment, price_reduction=0):
    order = Order(status=OrderStatus.PAID if is_online_payment else OrderStatus.ORDERED,
                  price_reduction=price_reduction, customer_id=current_user.id)
    db.session.add(order)

    # Tạo các order_details
    order_items = []
    for book_id, item in cart.items():
        if item.get('purchase_quantity'):
            order_detail = OrderDetail(order=order, book_id=book_id, price=item['price'],
                                       quantity=item['purchase_quantity'])
            db.session.add(order_detail)

            # Thêm thông tin mặt hàng vào danh sách
            book = Book.query.get(book_id)
            if book:
                order_items.append(f"- {book.title}: {item['purchase_quantity']} x {item['price']} đ")

        # Cập nhật số lượng sản phẩm trong kho
        book = Book.query.get(book_id)
        if book:
            if book.quantity >= item['purchase_quantity']:
                book.quantity -= item['purchase_quantity']
            else:
                raise ValueError(f"Không đủ số lượng cho sách '{book.title}'.")

    db.session.commit()

    # Sau khi tạo đơn hàng thành công thì gởi mail cho Khách hàng đã thanh toán bằng paypal, hoặc đặt trước
    items_list = "\n".join(order_items)
    sub = 'Đơn đặt hàng của bạn được tạo thành công'
    content = f'''Xin chào {current_user.first_name} {current_user.last_name},
Đây là thông tin đơn hàng của bạn:
    Ngày tạo: {order.created_date.strftime('%d-%m-%Y %H:%M:%S')}
    Trạng thái: {order.status}
    Mặt hàng:
        {items_list}
Cảm ơn bạn đã mua hàng'''
    if order.customer_id:
        utils.send_mail(sub, content, [current_user.email])

    return order


def create_order_case_selling_at_store(cart, price_reduction=0):
    order = Order(status=OrderStatus.RECEIVED, price_reduction=price_reduction, staff_id=current_user.id)
    db.session.add(order)
    # Đoạn này lặp code với hàm trên
    # Tạo các order_details
    for book_id, item in cart.items():
        if item.get('purchase_quantity'):
            order_detail = OrderDetail(order=order, book_id=book_id, price=item['price'],
                                       quantity=item['purchase_quantity'])
            db.session.add(order_detail)

        # Cập nhật số lượng sản phẩm trong kho
        book = Book.query.get(book_id)
        if book:
            if book.quantity >= item['purchase_quantity']:
                book.quantity -= item['purchase_quantity']
            else:
                raise ValueError(f"Không đủ số lượng cho sách '{book.title}'.")
    db.session.commit()
    return order


def get_stats_by_cate_per_month(year=None):
    if year is None:
        year = datetime.datetime.now().year  # Mặc định lấy năm hiện tại

    result = db.session.query(
        Category.id,
        Category.name.label('category_name'),       # Cột category_name
        extract('month', Order.created_date).label('month'),  # Cột month
        func.sum(OrderDetail.price * OrderDetail.quantity).label('revenue')   # Cột revenue: tổng doanh thu của từng category_name
    ).join(Book, Book.id == OrderDetail.book_id) \
        .join(Book.categories)\
        .join(Order, Order.id == OrderDetail.order_id) \
        .filter(extract('year', Order.created_date) == year,
                or_(Order.status == OrderStatus.PAID, Order.status == OrderStatus.RECEIVED)) \
        .group_by(Category.id, Category.name, extract('month', Order.created_date)) \
        .order_by(Category.id, extract('month', Order.created_date)) \
        .all()
    return result


def get_order_of_user(status=None):
    orders = Order.query.filter_by(customer_id=current_user.id)
    if status:
        if status == 'ordered':
            status = OrderStatus.ORDERED
        if status == 'completed':
            status = OrderStatus.PAID
        if status == 'cancelled':
            status = OrderStatus.CANCELED

        orders = orders.filter(Order.status == status)

    result = [
        {'id': order.id, 'status': order.status.name}
        for order in orders.order_by(Order.id).all()
    ]

    return result


if __name__ == '__main__':
    with app.app_context():
        print(get_user_by_username('0gg'))
