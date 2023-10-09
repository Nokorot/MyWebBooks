
importpymongo
importsys
importos

fromdotenv import load_dotenv
frompprint import pprint 

#connect to mongodb
load_dotenv()
MONGODB_URI= os.environ['MONGODB_URI']

try:
client = pymongo.MongoClient(MONGODB_URI)
print("connected")

#return a friendly error if a URI error is thrown 
exceptpymongo.errors.ConfigurationError:
print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
sys.exit(1)

definsertOne(database: str, collection: str, document: dict):
coll = client[database][collection]
coll.insert_one(document)

deffindOne(database: str, collection:str, query: dict):
coll = client[database][collection]
return coll.find_one(query)

deffind(database: str, collection:str, query: dict):
coll = client[database][collection]
return coll.find(query)

defupdateOne(database: str, collection: str, query: dict, update: dict, **kwargs):
coll = client[database][collection]
coll.update_one(query, {"$set" : update }, **kwargs)

defdeleteOne(database: str, collection: str, query: dict):
coll = client[database][collection]
coll.delete_one(query)

