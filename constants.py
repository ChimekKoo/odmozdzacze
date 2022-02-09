API_CURRENT_VERSION = "1"
API_ENTRYPOINT = f"/api/v{API_CURRENT_VERSION}"
DEBUG = True # There's a bug: cannot iterate over cursor object returned by categories_col.find() when DEBUG == False.
ALPHANUMERIC = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
API_TOKEN_SIZE = 64