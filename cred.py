from os import environ

def get_cred():

    return {
        "mongodb_url": environ.get("ODMOZDZACZE_MONGODB_URL"),
        "secret_key": environ.get("ODMOZDZACZE_SECRET_KEY")
    }
