
from bson.objectid import ObjectId
import src.mongodb_api_1 as mongodb_api
import functools

from src.webpages import get_wm_class, match_url
from src.user_data import get_user_name, get_user_sub

def load_bookdata(id_name='id', book_data_name='book'):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            id = kwargs.get(id_name)
            book_data = BookData(id)
            kwargs[book_data_name] = book_data
            result = func(*args, **kwargs)
            book_data.push()
            return result;
        return wrapped_func
    return decorator

def get_user_books():
    # TAG: USER_NAME2SUB

    # List _OLD_ type entries
    name_query = {'owner': get_user_name(), 'owner_sub': None}
    for book in mongodb_api.find('rr', 'books', name_query):
        # Converts this entry to _NEW_ type
        mongodb_api.updateOne('rr', 'books', book, \
                {'$set':   {'owner_sub': get_user_sub()}, \
                 '$unset': {'owner': None }})

    # List _NEW_ type entries
    user_sub_query = {'owner_sub': get_user_sub()}
    for book in mongodb_api.find('rr', 'books', user_sub_query):
        with BookData(book['_id'], book) as bd:
            yield bd

def add_new_book_entry(wm_class_name, data_entries):
    mongodb_api.insertOne('rr', 'books', {
        'owner_sub' : get_user_sub(),
        'wm_class_name': wm_class_name,
        **data_entries,
        })

class BookData():
    def __init__(self, id, mongod_data=None):
        self.id = id
        if mongod_data is None:
            obj_id = ObjectId(self.id)
            mongod_data = mongodb_api.findOne('rr', 'books', {'_id': obj_id})
        self.mongod_data = mongod_data
        self.wm = None

        # TAG: USER_NAME2SUB
        # This is probably unnecessary
        if mongod_data.get('owner_sub') is None:
            owner_name = mongod_data.get('owner')
            if owner_name == get_user_name():
                mongodb_api.updateOne('rr', 'books', \
                        {'$set':   {'owner_sub': get_user_sub()}, \
                         '$unset': {'owner': None }})
                mongod_data.set('owner_sub', get_user_sub())

        # NOTE: We are assuming mongod_data agrees with the one on mongodb.
        #   It is used when we loop through the entries of find in list_books
        self.dirty = False

    def push(self):
        if self.dirty:
            self.dirty = False
            print("DEBUG: Updating database, book {}".format(self.mongod_data['title']))

            obj_id = ObjectId(self.id)
            mongodb_api.setOne('rr','books', {'_id': obj_id}, self.mongod_data)

    close = push # deprecated: alias


    def get(self, key, default=None):
        return self.mongod_data.get(key, default)

    def set(self, key, value):
        if self.mongod_data.get(key) == value:
            return
        self.dirty = True
        self.mongod_data[key] = value

    def delete(self):
        obj_id = ObjectId(self.id)
        mongodb_api.deleteOne('rr', 'books', {"_id": obj_id})

    def get_wm_class(self):
        wm_class_name = self.get('wm_class_name')
        if not wm_class_name is None:
            return get_wm_class(wm_class_name)
        entry_point = self.get('entry_point')
        if entry_point is None:
            return None
        wm_class, _ = match_url(entry_point)
        self.set('wm_class_name', wm_class.__name__)
        return wm_class

    def get_wm(self):
        if self.wm is not None:
            return self.wm
        wm_class = self.get_wm_class()
        if wm_class is None:
            return None

        self.wm = wm_class(self.id, self)
        return self.wm

    def is_owner(self):
        return self.mongod_data.get('owner_sub') == get_user_sub()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __enter__(self):
        return self

    def __exit__(self, etype, value, tb):
        if tb is None:
            self.push()
            # No Exception occurred
            return
