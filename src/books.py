
from flask import Blueprint
blueprint = Blueprint("books", __name__)

from datetime import datetime

from flask import render_template, request, url_for, redirect, g, session, flash
from bson.objectid import ObjectId

from src.mongodb_api_1 import *
from src.auth import login_required

@blueprint.route('/new_book', methods=['GET', 'POST'])
@login_required
def new_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        cover_image = request.form.get('cover_image')
        entry_point = request.form.get('entry_point')
        rss = request.form.get('rss')
        section_css_selector = request.form.get('section_css_selector')
        title_css_selector = request.form.get('title_css_selector')
        paragraph_css_selector = request.form.get('paragraph_css_selector')
        next_chapter_css_selector = request.form.get('next_chapter_css_selector')

        insertOne('rr', 'books',
            {
                #added by the system
                'owner_id' : g.user['_id'],
                'last_update' : datetime.now(),
                #collected from form
                'title' : title,
                'author' : author,
                'cover_image' : cover_image,
                'entry_point' : entry_point,
                'rss' : rss,
                'section_css_selector' : section_css_selector,
                'title_css_selector' : title_css_selector,
                'paragraph_css_selector' : paragraph_css_selector,
                'next_chapter_css_selector' : next_chapter_css_selector
            }
        )
        flash('New data instance created successfully!')
        
        #return redirect(url_for('books.edit_book/%s' % id))
 
    data = {
        "title": {'label': "Title", "name": "title", 'text': "" },
        "author": {'label': "author", "name": "author", 'text': "" },
        "cover_image": {'label': "Cover Image URL", "name": "cover_image", 'text': "" },
        "entry_point": {'label': "Starting URL", "name" : "entry_point", 'text': "royalroad.com" },
        "rss": {'label': "RSS URL", 'name': "rss", 'text': "" },
        "section_css_selector": {'label': "Section CSS selector","name": "section_css_selector", 'text': "" },
        "title_css_selector": {'label': "Title CSS selector", 'name': "title_css_selector", 'text': "" },
        "paragraph_css_selector": {'label': "Paragraph CSS selector", "name":"paragraph_css_selector",'text': "" },
        "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'name': "next_chapter_css_selector", 'text': "" }
    }
    kwargs = {
            "TITLE": "New Book",
            "DERCRIPTION": "",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": ""
    }

    return render_template('data_form.html', **kwargs)


@blueprint.route('/edit_book/<id>', methods=['GET', 'POST'])
@login_required
def edit_data(id):
    id = ObjectId(id)

    if request.method == 'POST':
        # Update the JSON data with the form values

        import json
        with open("data/empty_book_form.json", 'r') as f:
            book_form_template = json.load(f)
        form = request.form
        
        for key in book_form_template.keys():
            book_form_template[key] = form.get(key)
        
        updateOne('rr','books', {'_id': id}, book_form_template)
        flash("data updated!")
        return 'Data updated successfully.'


    # Retrieve the data from MongoDB
    book = findOne('rr', 'books', {'_id': id})

    data = {
        "title": {'label': "Title", "name": "title"},
        "author": {'label': "author", "name": "author"},
        "cover_image": {'label': "Cover Image URL", "name": "cover_image"},
        "entry_point": {'label': "Starting URL", "name" : "entry_point", 'text': "royalroad.com" },
        "rss": {'label': "RSS URL", 'name': "rss", 'text': "" },
        "section_css_selector": {'label': "Section CSS selector","name": "section_css_selector", 'text': "" },
        "title_css_selector": {'label': "Title CSS selector", 'name': "title_css_selector", 'text': "" },
        "paragraph_css_selector": {'label': "Paragraph CSS selector", "name":"paragraph_css_selector",'text': "" },
        "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'name': "next_chapter_css_selector", 'text': "" }
    }
    for key, value in data.items():
        data[key]["text"] = book[key]


    kwargs = {
            "TITLE": "Edit Data",
            "DERCRIPTION": "",
            "SUBMIT": "Save",
            "DATA": data,
            "NO_REDIRECT_ONSUBMIT": True,
            "INCLUDE_IMPORT_EXPORT": True,
            "ACTION": url_for('books.edit_data', id=id),
    }
    return render_template('data_form.html', **kwargs)

@blueprint.route('/list_books', methods = ['GET'])
def list_books():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    books_list = []

    if g.user:
        books = find('rr', 'books', {'owner_id': g.user['_id']})

        # Prepare the data list to pass to the template
        for book in books:
            books_list.append({
                '_id': book['_id'],
                'title': book['title']
            })
    else:
        flash('Not logged in!')

    return render_template('books.html', data_list=books_list)

@blueprint.route('/delete_book/<id>', methods = ['POST'])
@login_required
def delete_book(id):
    id = ObjectId(id)
    deleteOne('rr', 'books', {"_id": id})
    return redirect('../list_books')



