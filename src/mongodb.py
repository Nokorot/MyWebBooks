import requests
import json

# SEE: https://www.mongodb.com/docs/atlas/api/data-api-resources/#delete-multiple-documents
class mongodb_api():
    
    def __init__(self, base_url, db_info, api_key):
        self.base_url = base_url
        self.db_info = db_info
        self.headers = {
          'Content-Type': 'application/json',
          'Access-Control-Request-Headers': '*',
          'api-key': api_key
        }

    @staticmethod
    def from_json(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return mongodb_api(data['base_url'], data['db_info'], data["api_key"])
    
    def _request(self, action, data):
        payload = json.dumps(self.db_info | data)
        
        url = self.base_url + action
        response = requests.request("POST", url, headers=self.headers, data=payload)
        return json.loads(response.text)
    
    def findOne(self, filter, **kwargs):
        return self._request("findOne", { "filter":  filter } | kwargs)
    
    def find(self, filter, **kwargs):
        return self._request("find", { "filter":  filter } | kwargs)
    
    def insertOne(self, document, **kwargs):
        return self._request("insertOne", { "document":  document } | kwargs)
    
    def insertMany(self, documents, **kwargs):
        return self._request("insertMany", { "documents":  documents } | kwargs)
    
    def updateOne(self, filter, update, **kwargs):
        return self._request("updateOne", { "filter":  filter, "update": update } | kwargs)
    
    def replaceOne(self, filter, replacement, **kwargs):
        return self._request("replaceOne", { "filter":  filter, "replacement": replacement } | kwargs)
    
    def updateMany(self, filter, update, **kwargs):
        return self._request("updateMany", { "filter":  filter, "update": update } | kwargs)
    
    def deleteOne(self, filter):
        return self._request("deleteOne", { "filter":  filter })
    
    def deleteMany(self, filter):
        return self._request("deleteMany", { "filter":  filter })
