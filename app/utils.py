from flask import session
from db import admins_col, banners_col

from random import randint, choice
import json
import email_validator
from constants import ALPHANUMERIC, API_TOKEN_SIZE
import bcrypt
import requests

def generate_id(ids):
    while True:
        random_number = randint(100000000, 999999999)
        if random_number not in ids:
            return str(random_number)

def generate_api_token(tokens):
    while True:
        random_token = "".join(choice(ALPHANUMERIC) for _ in range(API_TOKEN_SIZE))
        if random_token not in tokens:
            return random_token

def is_logged():
    count = admins_col.count_documents({"login": session.get("login", "")})
    return count > 0

def hash_psw(psw):
    return bcrypt.hashpw(psw.encode(), bcrypt.gensalt()).decode("utf8")

def check_hashed_psw(psw, hashed):
    return bcrypt.checkpw(psw.encode(), hashed.encode())


def cursor_to_list(cursor, cursor_filter=""):
    if cursor_filter == "":
        array = []
        for i in cursor:
            array.append(i)
        return array
    else:
        array = []
        for i in cursor:
            array.append(i[cursor_filter])
        return array

def request_form_to_dict(available_request_form):
    request_args = {}

    for request_arg in available_request_form.keys():
        if request_arg in request.args.keys():
            request_args[request_arg] = request.form[request_arg]
        else:

            request_args[request_arg] = available_request_form[request_arg]

    return request_args


def check_profanity(text):
    with open("static/profanities.json", mode="r") as f:
        contents = f.read()
        profanities = json.loads(contents)
    
    for i in profanities:
        if i in text:
            return True
    else:
        return False

def valid_email(email):
    try:
        email_validator.validate_email(email)
    except email_validator.EmailNotValidError:
        return False
    return True

def is_human(frontend_resp, secret):
    if frontend_resp is None: return False

    resp = json.loads(requests.post("https://www.google.com/recaptcha/api/siteverify", data={
        "secret": secret,
        "response": frontend_resp
    }).text)

    return resp["success"]

def get_banners():
    banners = cursor_to_list(banners_col.find())
    return banners
