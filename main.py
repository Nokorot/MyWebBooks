
import os, sys

from flask import Flask, jsonify, render_template, send_file, request

from mongodb import mongodb_api

sys.path.insert(0, './html_to_epub')

from html_to_epub.RR_rss import load_datafile, getOldestNew, getChapters

from sendToKindle import main as sendToKindle

app = Flask(__name__)

if not os.path.exists('./out'):
    os.makedirs("./out")

@app.template_filter('get')
def get_value(dictionary, key):
    return dictionary.get(key, "")

@app.template_filter('generate_form_entry')
def generate_form_entry(data, key, name):
    print(data)
    value = data.get(name, "")
    form_entry = f'<div class="form-row"><label class="label" for="{name}">{key.capitalize()}:</label><div class="input-field"><input type="text" id="{name}" name="{name}" value="{value}" required></div></div>'
    return form_entry

@app.route('/RR_rss/<id>')
def RR_rss(id):
    # new, epub_file = load_datafile('./books/IR.yaml')
    db_api = mongodb_api.from_json("data/mongodb.json")
    data = db_api.findOne({'id': id})['document']
    if not data:
        return f"Unknown id {id}"
    from datetime import datetime
    from dateutil import parser as date_parser
    # https://www.royalroad.com/fiction/syndication/36299
    url = data.get('rss');
    lastTime = data.get('lastTime')
    if lastTime:
        lastTime = date_parser.parse(lastTime)

    oldestNew = getOldestNew(url, lastTime)
    if not oldestNew:
        return "No Updates!"

    epub_filename = f"/tmp/{id}-%date.epub"
    nowTime = datetime.now().isoformat(timespec='seconds') + '+0000'

    db_api.updateOne({'id': id}, {'$set': {"lastTime": nowTime}})


    data['epub_filename'] = epub_filename
    data['css_filename'] = "books/kindle.css"

    epub_file = getChapters(oldestNew['link'], 
                          { 'cache': f'/tmp/{id}', 
                           'callbacks': 'books.IR.Callbacks',
                           'book': data });

    with open("out/latest.txt", "w") as f:
        f.write(epub_file)

    sendToKindle(epub_file)

    return f"""
    <html> <p>A new update was sent to the kindle <p>
    <a href="/dl-latest-epub" target="blank"><button class='btn btn-default'>Download!</button></a>
    """

@app.route('/dl-latest-epub')
def dl_latest_epub():
    with open("out/latest.txt", "r") as f:
        epub_file = f.read()
    # epub_file = 'out/IR-2023-01-24.epub'
    print(epub_file)

    return send_file(epub_file)


@app.route('/new_book', methods=['GET', 'POST'])
def new_book():
    if request.method == 'POST':
        id = request.form.get('id')
        # Handle the creation of a new data instance with the specified ID
        flash('New data instance created successfully!')
        return redirect(url_for('edit_book/%s' % id))
    
    return render_template('new_book.html', data={"id": {'label': "ID", 'text': "" }})


@app.route('/edit_book/<id>', methods=['GET', 'POST'])
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

        # data = {
        #     'id': id,
        #     'title': request.form.get('title'),
        #     'author': request.form.get('author'),
        #     'epub_filename': request.form.get('epub_filename'),
        #     'cover_image': request.form.get('cover_image'),
        #     'css_filename': request.form.get('css_filename'),
        #     'rss': request.form.get('rss'),
        #     'entry_point': request.form.get('entry_point'),
        #     'chapter': {
        #         'section_css_selector': request.form.get('section_css_selector'),
        #         'title_css_selector': request.form.get('title_css_selector'),
        #         'text_css_selector': request.form.get('text_css_selector'),
        #         'next_chapter_css_selector': request.form.get('next_chapter_css_selector'),
        #     },
        #     'include_images': bool(request.form.get('include_images'))
        # }

        print(data)

        # Update or insert the data into the MongoDB collection
        # collection.replace_one({}, data, upsert=True)
        # collection.update_one({'id': id}, {'$set': data}, upsert=True)
        db_api.updateOne({'id': id}, {'$set': data}, upsert=True)
        
        return 'Data updated successfully.'

    # Retrieve the data from MongoDB
    data = db_api.findOne({'id': id})['document']
    if not data:
        data = {'chapter':{}}
        # with open("data/empty_book_data.json", r) as f:
        #     data = json.load(f)
    
    import json
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

    # Render the template with the current JSON data
    return render_template('edit_book.html', id=id, data=template_data)

@app.route('/list_books')
def data_list():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    db_api = mongodb_api.from_json("data/mongodb.json")
    data_instances = db_api.find({})['documents']
    print(data_instances)

    # Prepare the data list to pass to the template
    data_list = []
    for data in data_instances:
        data_list.append({
            'id': data['id'],
            'title': data['title']
        })

    return render_template('books.html', data_list=data_list)


@app.route('/', methods=['GET', 'POST'])
def index():
    # db_api = mongodb_api.from_json("data/mongodb.json")

    if request.method == 'POST':
        os.system(request.form.get("cmd"))
        
    import os
    return os.getcwd() #db_api.find({})

    # return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
