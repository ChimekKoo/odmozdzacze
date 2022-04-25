from pymongo import MongoClient
from cred import get_cred

cred = get_cred()

mongo_client = MongoClient(cred["mongodb_url"])#, connect=False)
db = mongo_client["odmozdzacze"]

reports_col = db["reports"]
categories_col = db["categories"]
admins_col = db["admins"]
