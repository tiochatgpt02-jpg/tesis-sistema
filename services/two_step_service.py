import random
import string
from datetime import datetime, timedelta


def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def code_expiration_time(minutes=10):
    return datetime.now() + timedelta(minutes=minutes)


def is_code_valid(submitted_code, stored_code, expiration_time):
    if not stored_code or not expiration_time:
        return False
    return submitted_code == stored_code and datetime.now() <= expiration_time
