from models import *
import datetime


#                        USER
def get_user_by_id(id):
    return Customer.query.get(id)


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
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    customer = Customer(username=username, password=password, phone_number=phone_number, first_name=first_name,
                        last_name=last_name, email=email ,address=address)
    db.session.add(customer)
    db.session.commit()
    return get_user_by_id(customer.id)

#                        PRODUCT
