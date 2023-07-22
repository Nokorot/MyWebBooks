
from flask import Blueprint
blueprint = Blueprint("books", __name__)

from flask import render_template, request, url_for, redirect, g, session
from bson.objectid import ObjectId
import json 
from .mongodb_api_1 import *

@blueprint.route('/new_book', methods=['GET', 'POST'])
def new_book():
    if request.method == 'POST':
        id = request.form.get('title')
        # Handle the creation of a new data instance with the specified ID
        flash('New data instance created successfully!')
        return redirect(url_for('books.edit_book/%s' % id))
 
    data = {"title": {'label': "Title", 'text': "" }}
    kwargs = {
            "TITLE": "New Book",
            "DERCRIPTION": "",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": url_for('books.new_book'),
    }

    return render_template('data_form.html', **kwargs)


@blueprint.route('/edit_book/<id>', methods=['GET', 'POST'])
def edit_data(id):
    id = ObjectId(id)
    db_api = mongodb_api.from_json("data/mongodb.json")

    if request.method == 'POST':
        # Update the JSON data with the form values
        import json
        with open("data/book_data.json", 'r') as f:
            fields = json.load(f)

        def gen_data_from_form(fields, form):
            data = {}
            for key, entry in fields.items():
                print(key, type(entry))
                if type(entry) == str:
                    # TODO: Check type of value
                    data[key] = form.get(key)
                if type(entry) == bool:
                    data[key] = form.get(key)
                elif type(entry) == dict:
                    if 'data' in entry:
                        data[key] = gen_data_from_form(entry['data'], form)
            return data
        data = gen_data_from_form(fields, request.form)
        data['_id'] = id


        # Update or insert the data into the MongoDB collection
        # collection.replace_one({}, data, upsert=True)
        # collection.update_one({'id': id}, {'$set': data}, upsert=True)
        db_api.updateOne({'_id': id}, {'$set': data}, upsert=True)
        
        return 'Data updated successfully.'

    def gen_template_fields_data(fields, data):
        template_data = {}
        for key, value in fields.items():
            print("HERE", key, type(value))
            if type(value) == str:
                # TODO: Check type of value
                template_data[key] = {'label': value, 'type': "str", 'text': data.get(key)}
            elif type(value) == dict:
                if not 'label' in value:
                    value.label = ''
                if 'data' in value:
                    value['data'] = gen_template_fields_data(value['data'], data.get(key))
                template_data[key] = value
        return template_data

    # Retrieve the data from MongoDB
    data = db_api.findOne({'_id': id})['document']
    if not data:
        data = {'chapter':{}}
    
    import json
    with open("data/book_data.json", 'r') as f:
        fields = json.load(f)

    template_data = gen_template_fields_data(fields, data)


    kwargs = {
            "TITLE": "Edit Data",
            "DERCRIPTION": "",
            "SUBMIT": "Save",
            "DATA": template_data,
            "NO_REDIRECT_ONSUBMIT": True,
            "INCLUDE_IMPORT_EXPORT": True,
            "ACTION": url_for('books.edit_data', id=id),
    }

    print(template_data)
    return render_template('data_form.html', **kwargs)

@blueprint.route('/list_books')
def list_books():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    
    books = find('rr', 'books', {'owner_id': g.user['_id']})

    # Prepare the data list to pass to the template
    data_list = []
    for book in books:
        data_list.append({
            '_id': book['_id'],
            'title': book['title']
        })

    return render_template('books.html', data_list=data_list)

@blueprint.route('/delete_book/<id>', methods = ['POST'])
def delete_book(id):
    id = ObjectId(id)
    db = mongodb_api.from_json("data/mongodb.json")
    db.deleteMany({"id": id})
    import json
    return redirect('../list_books')