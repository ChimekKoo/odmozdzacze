from os import environ
from dotenv import load_dotenv

load_dotenv()

def get_cred():

    cred = {
        "mongodb_url": environ.get("ODMOZDZACZE_MONGODB_URL"),
        "secret_key": environ.get("ODMOZDZACZE_SECRET_KEY"),
        "recaptcha_secret_key": environ.get("ODMOZDZACZE_RECAPTCHA_SECRET_KEY"),
        "recaptcha_site_key": environ.get("ODMOZDZACZE_RECAPTCHA_SITE_KEY")
    }
    
    # for x in cred.values():
    #     if x is None:
    #         raise EnvironmentError("Missing environment variable")
    
    return cred
