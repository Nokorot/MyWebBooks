
from flask import Blueprint
blueprint = Blueprint("books", __name__)

from flask import render_template, request, url_for, redirect
from .mongodb import mongodb_api

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
                if type(entry) in [str, bool]:
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


@blueprint.route('/download_book/<id>')
def download_book(id):  
    def gen_config(id, data):
        db_api = mongodb_api.from_json("data/mongodb.json")
        data = db_api.findOne({'id': id})['document']

        # FOLDERNAME = hash_url
        config = {}
        config['cache'] = f'cache/{id}'
        config['ignore_cache'] = False # data.get('ignore_cache', True)

        # config['callbacks'] = "books.RR_Template.cbs_base"

        book = { 
            "title"           : data["title"],
            "author"          : data["author"],
            "epub_filename"   : f'out/{id}.epub',
            "cover_image"     : data["cover_image"],
            "css_filename"    : "webbook_dl/kindle.css",
            "entry_point"     : data["entry_point"],
            "chapter"         : data['chapter'],
            "include_images"  : data["include_images"],
        }

        config['book'] = book 
        return config

    from html_to_epub import Config, Book
    config = Config(gen_config(id, request.form))
    config.ignore_last_cache = True

    import os
    os.makedirs(config.cache, exist_ok=True)

    # Still relative
    from books.RR_Template.cbs_base import Callbacks
    book = Book(config, Callbacks(config))

    book.load_html()

    print(config.book.epub_filename)

    from ebooklib import epub
    epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
 

    from RR_cnf_gen import foldername_from_title
    epub_filename = "%s.epub" % foldername_from_title(book.title)

    return redirect(url_for("royalroad_dl.download_book_submit", id=id, epub_filename=epub_filename))


@blueprint.route("/", methods=['GET', 'POST'])
def head():
    kwargs = {
            "TITLE": "RoyalRoad Book Download",
            "DERCRIPTION": "Enter the url to the fiction page of a royalroad book",
            "SUBMIT": "Submit",
            "DATA": {'fiction_page_url': {'label': 'Url', 'type': 'str', 'text': ''}},
            "ACTION": url_for("royalroad_dl.book_config"),
    }
    return render_template('data_form.html', **kwargs)


def royalroad_cofig_from_fiction_page(url, ignoe_cache = False):
    from html_to_epub.util import Network
    from lxml.cssselect import CSSSelector

    from RR_cnf_gen import first_match, foldername_from_title

    base_url = "https://www.royalroad.com"
    cache_dir = "./cache/RR"
    import os
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_filename = Network.cache_filename(cache_dir, url)


    tree = Network.load_and_cache_html(url, cache_filename, ignoe_cache)

    result = {}
    result['TITLE']   = first_match(tree, "div.fic-header h1").text;
    result['AUTHOR']  = first_match(tree, "div.fic-header h4 a").text;
    result['COVER']   = first_match(tree, "div.fic-header img").get('src').split('?')[0];
    result['ENTRY']   = base_url + first_match(tree, "div.portlet table a").get('href').split('?')[0];
    result['OUTFILE'] = foldername_from_title(result['TITLE'])

    print(result)
    return result

@blueprint.route("/configure-book", methods=['GET', 'POST'])
def book_config():
    data = {
        "TITLE"      : {'label': 'Title',          },
        "AUTHOR"     : {'label': 'Author',         },
        "COVER"      : {'label': 'Cover',          },
        "ENTRY"      : {'label': 'First Chapeter', },
        "INCLUDE_IMG"  : {'label': 'Include Images', 'type': 'bool', 'value': False },
        #  "OUTFILE"    : {'label': 'Epub File Name', },
    }

    if request.method == 'POST':
        request_data = request.form

        fiction_page_url = request_data.get("fiction_page_url");
        if not fiction_page_url: 
            return "ERROR: No 'fiction_page_url' was privided. Go to <a href=\"" +  \
                    url_for("royalroad_dl.head") +"\">royalroad-dl</a>"

        from urllib.parse import urlparse
        
        parsed_url = urlparse(fiction_page_url)
        path_parts = parsed_url.path.split("/")
        fiction_id = path_parts[2] if len(path_parts) > 2 else None

        if not fiction_id: 
            return "ERROR: Failed to parse 'fiction_page_url'. Go to <a href=\"" +  \
                    url_for("royalroad_dl.head") +"\">royalroad-dl</a>"

        id = fiction_id;

        if fiction_page_url:
            request_data = royalroad_cofig_from_fiction_page(fiction_page_url)

        for key in data.keys():
            value = request_data.get(key)
            if value: 
                data[key]['text'] = value

    kwargs = {
            "TITLE": "RoyalRoad Book Configuration",
            "DERCRIPTION": "Please check that the following configuration is correct (Note that after clicking, you just have to wait, sorry for the lack of visual indication)",
            "SUBMIT": "Download",
            "DATA": data,
            "NO_REDIRECT_ONSUBMIT": False,
            # "ACTION": url_for("royalroad_dl.book_config"),
            "ACTION": url_for("royalroad_dl.download_book", id=id),
    }
    return render_template('data_form.html', **kwargs)

@blueprint.route('/list_books')
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

