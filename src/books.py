from datetime import datetime
import requests

from flask import Blueprint
blueprint = Blueprint("books", __name__)

from bs4 import BeautifulSoup 
from flask import render_template, request, url_for, redirect, g, session, flash, send_from_directory, send_file
from bson.objectid import ObjectId
from ebooklib import epub

import os
import src.mongodb_api_1 as mongodb_api # import *
from src.login import login_required

import src.user_data as user_data

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
       
        from urllib.parse import urlparse 

        book_url = request.form['entry_point']
        r = requests.request('GET', book_url)
        if r.status_code != 200:
            print("page does not exists!")
            return 
        else:
            book_html = BeautifulSoup(r.text)
            print(urlparse(entry_point).netloc)
            is_royalroad = urlparse(entry_point).netloc.split('.')[1] == 'royalroad'
        


        mongodb_api.insertOne('rr', 'books',
            {
                #added by the system
                'owner' : g.user['userinfo']['name'],
                'last_update' : datetime.now(),
                #collected from form
                'title' :  book_html.select_one('div.fic-title h1').text if title == '' else title,
                'author' : book_html.select_one('div.fic-title a').text if author == '' else author,
                'cover_image' : book_html.select_one('img.thumbnail').get('src') if cover_image == '' else cover_image,
                'entry_point' : entry_point,
                'rss' : rss,
                'section_css_selector' : "div.fic-header h1.font-white" if is_royalroad else '',
                'title_css_selector' : "div.fic-header h1.font-white" if is_royalroad else '',
                'paragraph_css_selector' : 'div.chapter-inner' if is_royalroad else '',
                'next_chapter_css_selector' : "div.col-md-offset-4 a.btn" if is_royalroad else ''
            }
        )
        flash('New book created successfully!')
        
 
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
            "ACTION": "",
            "USER_PIC": g.user['userinfo']['picture']
    }

    return render_template('forms/new_book.html', **kwargs)


@blueprint.route('/edit_book/<id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    id = ObjectId(id)
    book = mongodb_api.findOne('rr', 'books', {'_id': id})
    if book['owner'] != g.user['userinfo']['name']:
        redirect(url_for('books.list_books'))

    if request.method == 'POST':
        # Update the JSON data with the form values

        import json
        with open("data/empty_book_form.json", 'r') as f:
            book_form_template = json.load(f)
        form = request.form
        book_url = form['entry_point']
        r = requests.request('GET', book_url)
        if r.status_code != 200:
            print("page does not exists!")
        else:
            book_html = BeautifulSoup(r.text)
        

        for key in book_form_template.keys():
            book_form_template[key] = form.get(key)
            if book_form_template[key] == '':
                if key == 'cover_image':
                        book_form_template[key] = book_html.select_one('img.thumbnail').get('src')
                elif key == 'title':
                        book_form_template[key] = book_html.select_one('div.fic-title h1').text
                elif key == 'author':
                        book_form_template[key] = book_html.select_one('div.fic-title a').text 
                
                
        mongodb_api.updateOne('rr','books', {'_id': id}, book_form_template)
        flash("data updated!")
        return 'Data updated successfully.'


    # Retrieve the data from MongoDB
    book = mongodb_api.findOne('rr', 'books', {'_id': id})

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
            "ACTION": url_for('books.edit_book', id=id),
    }
    return render_template('data_form.html', **kwargs)

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

@blueprint.route('/list_books', methods = ['GET'])
def list_books():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    books_list = []

    if g.user:
        books = mongodb_api.find('rr', 'books', {'owner': g.user['userinfo']['name']})

        # Prepare the data list to pass to the template
        for book in books:
            books_list.append({
                '_id': book['_id'],
                'title': book['title'],
                'img_url': book['cover_image']
            })
    else:
        flash('Not logged in!')

    return render_template('books.html', data_list=books_list)

@blueprint.route('/delete_book/<id>')
@login_required
def delete_book(id):
    id = ObjectId(id)
    book = mongodb_api.findOne('rr', 'books', {'_id': id})
    if book['owner'] != g.user['userinfo']['name']:
        redirect(url_for('books.list_books'))
    mongodb_api.deleteOne('rr', 'books', {"_id": id})
    return redirect('../list_books')





@blueprint.route('download_epub/<id>')
@login_required
def download_epub(id):
    download_book_to_server(id)
    book = mongodb_api.findOne('rr', 'books', {'_id': ObjectId(id)})
    
    try:
        print('SENDING!')
        return send_from_directory('out', '{}.epub'.format(book.get('title')), as_attachment = True)
    except:
        flash('file not found')
        return url_for('books.list_books')
    #return redirect(url_for('books.list_books'))



from .sendToKindle import sendToKindle
@blueprint.route('send_to_kindle/<id>')
@login_required
def send_to_kindle(id):
    ebook_file = download_book_to_server(id)
    book = mongodb_api.findOne('rr', 'books', {'_id': ObjectId(id)})

    # user = get_user_auth0_info()
    # kindle_address = user['user_metadata']['kindle_address'])

    kindle_address = user_data.get_kindle_address()

    print(kindle_address, '####')
    if not kindle_address:
        flash('The kindle email address was not set. Please enter and submit your kindle email address');
    else:
        sendToKindle(file = ebook_file,
                     target_filename='{}.epub'.format(book['title']),
                     receiver = kindle_address);
        flash('The email has been sent successfully')
    return redirect(url_for('books.list_books')) 




@blueprint.route('test')
def test():
    user = user_data.get_auth0_info()
    user['user_metadata']['kindle_address']
    
    return 'hello', 200


# TODO: This function should take the book data as an augment no the book id
def download_book_to_server(id):
    book = mongodb_api.findOne('rr', 'books', {'_id': ObjectId(id)})

    local_ebook_filepath = 'out/{}.epub'.format(book.get('title'))

    #if already in server
    if(os.path.exists(local_ebook_filepath)):
        return local_ebook_filepath

    ebook = epub.EpubBook()
    # mandatory metadata
    ebook.set_identifier(id)
    ebook.set_title(book.get('title'))
    ebook.set_language('en')
    ebook.add_author(book.get('author'))
    #collect chapters
    start = BeautifulSoup(requests.get(book.get('entry_point')).text)
    chapters = start.select('table#chapters a')
    for index, chapter in enumerate(chapters):
        print(f'downloading chapter {index}')
        chapter_page = BeautifulSoup(requests.get('https://www.royalroad.com' + chapter.get('href')).text)
        temp_chapter = epub.EpubHtml(title = chapter.get('innerHTML'),
                                     file_name = f'chapter_{index}.xhtml')
        temp_chapter.set_content(
            str(chapter_page.select_one('h1')) +
            ''.join([str(x) for x in chapter_page.select('div.chapter-content p')])
        )
        ebook.add_item(temp_chapter)
        ebook.toc.append(temp_chapter)
        ebook.spine.append(temp_chapter)

    print('chapters packed')
    ebook.add_item(epub.EpubNcx())
    ebook.add_item(epub.EpubNav())
    epub.write_epub('out/{}.epub'.format(book.get('title')), ebook)
    print('book in the server')
    return



