API_CURRENT_VERSION = "1"
API_ENTRYPOINT = f"/api/v{API_CURRENT_VERSION}"
DEBUG = False # Do not commit to master branch when DEBUG = True
ALPHANUMERIC = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
API_TOKEN_SIZE = 64
BLANK_REPORTDICT = {
    "id": "",
    "edittime": "",
    "inserttime": "",
    "category": "",
    "name": "",
    "content": "",
    "email": "",
    "verified": ""
}