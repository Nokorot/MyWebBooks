
from flask import Blueprint
blueprint = Blueprint("books", __name__)

from flask import render_template, request, url_for
from .mongodb import mongodb_api
import json 

@blueprint.route('/new_book', methods=['GET', 'POST'])
def new_book():
    if request.method == 'POST':
        id = request.form.get('id')
        # Handle the creation of a new data instance with the specified ID
        flash('New data instance created successfully!')
        return redirect(url_for('books.edit_book/%s' % id))
 
    data = {"id": {'label': "ID", 'text': "" }}
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
        data['id'] = id


        # Update or insert the data into the MongoDB collection
        # collection.replace_one({}, data, upsert=True)
        # collection.update_one({'id': id}, {'$set': data}, upsert=True)
        db_api.updateOne({'id': id}, {'$set': data}, upsert=True)
        
        return 'Data updated successfully.'

    # Retrieve the data from MongoDB
    data = db_api.findOne({'id': id})['document']
    if not data:
        data = {'chapter':{}}
    
    with open("data/book_data.json", 'r') as f:
        fields = json.load(f)

    def gen_template_fields_data(fields, data):
        template_data = {}
        for key, entry in fields.items():
            print("HERE", key, type(entry))
            if type(entry) == str:
                value = data.get(key)
                # TODO: Check type of value
                template_data[key] = {'label': entry, 'type': "str", 'text': value}
            elif type(entry) == dict:
                if not 'label' in entry:
                    entry.label = ''
                if 'data' in entry:
                    entry['data'] = gen_template_fields_data(entry['data'], data.get(key))
                template_data[key] = entry
        return template_data
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
def data_list():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    db_api = mongodb_api.from_json("data/mongodb.json")
    data_instances = db_api.find({})['documents']
    #DEBUG
    #print('data instances: ')
    #print(json.dumps(data_instances, indent = 4))

    # Prepare the data list to pass to the template
    data_list = []
    for data in data_instances:
        data_list.append({
            'id': data['id'],
            'title': data['title']
        })


    return render_template('books.html', data_list=data_list)

