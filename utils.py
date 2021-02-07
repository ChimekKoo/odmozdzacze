from random import randint
from main import session, request


def generate_id(ids):
    while True:
        random_number = randint(100000000, 999999999)
        if random_number not in ids:
            return str(random_number)


def check_if_logged():
    try:
        session["logged"]
    except KeyError:
        logged = False
    else:
        if not session["logged"]:
            logged = False
        else:
            logged = True
    return logged


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


def request_args_to_dict(available_request_args):
    request_args = {}

    for request_arg in available_request_args.keys():
        if request_arg in request.args.keys():
            request_args[request_arg] = request.args[request_arg]
        else:
            request_args[request_arg] = available_request_args[request_arg]

    return request_args
