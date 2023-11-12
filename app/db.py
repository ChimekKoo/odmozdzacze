from pymongo import MongoClient
from os import environ
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(environ.get("ODMOZDZACZE_MONGODB_URL"))#, connect=False)
db = mongo_client["odmozdzacze"]

reports_col = db["reports"]
categories_col = db["categories"]
admins_col = db["admins"]
banners_col = db["banners"]
