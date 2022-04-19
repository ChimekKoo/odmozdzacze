from os import environ

def get_cred():

    cred = {
        "mongodb_url": environ.get("ODMOZDZACZE_MONGODB_URL"),
        "secret_key": environ.get("ODMOZDZACZE_SECRET_KEY"),
        "recaptcha_secret_key": environ.get("ODMOZDZACZE_RECAPTCHA_SECRET_KEY"),
        "recaptcha_site_key": environ.get("ODMOZDZACZE_RECAPTCHA_SITE_KEY")
    }
    
    return cred
