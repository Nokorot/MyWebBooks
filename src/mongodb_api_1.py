
import pymongo
import sys
import os

from dotenv import load_dotenv
from pprint import pprint

#connect to mongodb
load_dotenv()
MONGODB_URI= os.environ['MONGODB_URI']

try:
    client = pymongo.MongoClient(MONGODB_URI)
    print("connected")

    #return a friendly error if a URI error is thrown
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
    sys.exit(1)

def insertOne(database: str, collection: str, document: dict):
    coll = client[database][collection]
    coll.insert_one(document)

def findOne(database: str, collection:str, query: dict):
    coll = client[database][collection]
    return coll.find_one(query)

def find(database: str, collection:str, query: dict):
    coll = client[database][collection]
    return coll.find(query)

def updateMany(database: str, collection: str, query: dict, update: dict, **kwargs):
    coll = client[database][collection]
    coll.update_many(query, update, **kwargs)

def updateOne(database: str, collection: str, query: dict, update: dict, **kwargs):
    coll = client[database][collection]
    coll.update_one(query, update, **kwargs)

def setOne(database: str, collection: str, query: dict, update: dict, **kwargs):
    coll = client[database][collection]
    coll.update_one(query, {"$set" : update }, **kwargs)

def unsetOne(database: str, collection: str, query: dict, update: dict, **kwargs):
    coll = client[database][collection]
    coll.update_one(query, {"$unset" : update }, **kwargs)

def deleteOne(database: str, collection: str, query: dict):
    coll = client[database][collection]
    print(query)
    coll.delete_one(query)

