from models import *
import datetime


def get_user_by_id(id):
    user = Customer.query.get(id)
    staff = Staff.query.get(id)
    if user:
        return user
    return staff


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = Customer.query.filter(Customer.username.__eq__(username), Customer.password.__eq__(password))
    staff = Staff.query.filter(Staff.username.__eq__(username), Staff.password.__eq__(password))
    # filter() trả ra đối tượng query
    if user.first():
        return user.first()
    elif staff.first():
        staff.first().last_login_date = datetime.datetime.now()
        db.session.add(staff.first())
        db.session.commit()
        return staff.first()
    return None
