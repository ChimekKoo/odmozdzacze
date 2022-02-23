from os import environ
from exceptions import CredError

def get_cred():

    cred = {
        "mongodb_url": environ.get("ODMOZDZACZE_MONGODB_URL"),
        "secret_key": environ.get("ODMOZDZACZE_SECRET_KEY")
    }

    if cred["mongodb_url"] is None or cred["secret_key"] is None:
        raise CredError("Secrets in environment variables not defined.")
    
    return cred
