from os import environ
from json import loads

from constants import CRED_OR_ENVIRON, CRED_FILE_NAME


def get_cred():

    if CRED_OR_ENVIRON == "cred":
        try:
            with open(CRED_FILE_NAME, "r") as cred_file_obj:
                cred = loads(cred_file_obj.read())
                cred_file_obj.close()
            return cred
        except FileNotFoundError:
            print(CRED_FILE_NAME, "file does not exists (FileNotFoundError).")
            exit(1)

    elif CRED_OR_ENVIRON == "environ":

        cred = {
            "smtp": {
                "host": environ.get("SMTP_HOST"),
                "port": environ.get("SMTP_PORT"),
                "login": environ.get("SMTP_LOGIN"),
                "password": environ.get("SMTP_PASSWORD")
            },
            "mongodb_url": environ.get("MONGODB_URL"),
            "secret_key": environ.get("SECRET_KEY")
        }
        return cred

    else:
        raise ValueError("constants.CRED_OR_ENVIRON is not 'cred' or 'environ'.")
