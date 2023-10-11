from datetime import datetime
import requests

from flask import Blueprint
blueprint= Blueprint("books", __name__)

from bs4 import BeautifulSoup
from flask import render_template, request, url_for, redirect, g, session, flash, send_file, send_file
from bson.objectid import ObjectId
from ebooklib import epub

import os
import src.mongodb_api_1 as mongodb_api # import *
from src.login import login_required

import src.user_data as user_data

@blueprint.route('/new_book',methods=['GET', 'POST'])
@login_required
def new_book():
    if request.method == 'POST':
        entry_point = request.form.get('entry_point')

        from src.webpages import match_url
        wm_class = match_url(entry_point)

        if wm_class is None:
            # TODO: HERE we can ask the user whether they want to make a custom web-crawler

            flash("Unknown Entry point url! Only RoyalRoad is supported at the moment")
            return redirect(url_for('home'))

        # wm = wm_class.new_book(entry_point)

        mongodb_api.insertOne('rr', 'books', {
            'owner' : g.user['userinfo']['name'],
            'wm_class_name': wm_class.__name__,
            'entry_point' : entry_point,

            # wm.data_entries()
            })

        flash('New book created successfully!')
        return redirect(url_for('home'))

    data = {
        "entry_point": {
            'label': "Starting URL",
            'value': "royalroad.com" },
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


@blueprint.route('/edit_book/<id>',methods=['GET', 'POST'])
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
        "title": {'label': "Title"},
        "author": {'label': "author"},
        "cover_image": {'label': "Cover Image URL"},
        "entry_point": {'label': "Starting URL", 'value': "royalroad.com" },
        "rss": {'label': "RSS URL", 'value': "" },
        "section_css_selector": {'label': "Section CSS selector", 'value': "" },
        "title_css_selector": {'label': "Title CSS selector", 'value': "" },
        "paragraph_css_selector": {'label': "Paragraph CSS selector",'value': "" },
        "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'value': "" }
    }
    for key, value in data.items():
        data[key]["value"] = book[key]

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

@blueprint.route("/",methods=['GET', 'POST'])
def head():
    kwargs = {
    "TITLE": "RoyalRoad Book Download",
    "DERCRIPTION": "Enter the url to the fiction page of a royalroad book",
    "SUBMIT": "Submit",
    "DATA": {'fiction_page_url': {'label': 'Url', 'type': 'str', 'value': ''}},
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

@blueprint.route("/configure-book",methods=['GET', 'POST'])
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
                data[key]['value'] = value

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

@blueprint.route('/list_books',methods = ['GET'])
@login_required
def list_books():
    books_list = []

    # Prepare the data list to pass to the template
    for book in mongodb_api.find('rr', 'books', {'owner': g.user['userinfo']['name']}):
        wm_class_name = book.get('wm_class_name')
        if not wm_class_name is None:
            from src.webpages import get_wm_class
            wm_class = get_wm_class(wm_class_name)
        else:
            entry_point = book.get('entry_point')
            if entry_point is None:
                continue
            from src.webpages import match_url
            wm_class = match_url(entry_point)

            # TODO: Update mongodb entry
        if wm_class is None:
            # This should not happen
            continue

        wm = wm_class(book['_id'], book)

        books_list.append({
            '_id':     wm.id,
            'title':   wm.get_book_data('title'),
            'img_url': wm.get_book_data('cover_image')
        })

    return render_template('books.html', data_list=books_list)

@blueprint.route('/delete_book/<id>')
@login_required
def delete_book(id):
    id = ObjectId(id)
    book = mongodb_api.findOne('rr', 'books', {'_id': id})
    print(book, g.user['userinfo']['name'])
    if book['owner'] == g.user['userinfo']['name']:
        mongodb_api.deleteOne('rr', 'books', {"_id": id})
    return redirect(url_for('books.list_books'))

@blueprint.route('download_epub/<id>',methods=['GET', 'POST'])
@login_required
def download_epub(id):
    book = mongodb_api.findOne('rr', 'books', {'_id': ObjectId(id)})

    # Here the plan is to include the webpage_manager specified for this particular book on mongodb,
    # but it is hard-coded to royalroad for now.
    # from src.webpages.royalroad import RoyalRoad

    from src.webpages import get_wm_class
    wm_class = get_wm_class('RoyalRoadWM')
    webpage_manager = wm_class(id, book)

    # For example, we can have a book_crawler webpage_manager,
    # with custom css selectors for the chapter content, title ... and the next chapter button

    print("METHOD", request.method)
    if request.method == 'POST':
        # local_ebook_filepath = 'out/{}.epub'.format(book.get('title'))

        config_data = webpage_manager.parse_download_config_data_form(request.form)
        datahash = webpage_manager.genereate_download_config_hash(config_data)
        # TODO: Store the config_data along with the epub.

        local_epub_filepath = 'out/{}.epub'.format(datahash)

        # if now already in server download it
        # if(not os.path.exists(local_epub_filepath)):

        webpage_manager.download_book_to_server(config_data, local_epub_filepath)


        if request.form.get('sendToKindle'):
            from .sendToKindle import sendToKindle

            kindle_address = user_data.get_kindle_address()
            if not kindle_address:
                flash('The kindle email address was not set. Please enter and submit your kindle email address');
            else:
                sendToKindle(file = local_epub_filepath,
                        target_filename='{}.epub'.format(book['title']),
                        receiver = kindle_address);
                flash('The email has been sent successfully')
            return redirect(url_for('books.list_books'))

        try:
            print('SENDING! "%s"' % local_epub_filepath)
            return send_file(local_epub_filepath, as_attachment = True, \
                download_name="%s.epub" % config_data.get('title'))
        except Exception as e:
            print(e)
            print('SENDING FAILED!')
            flash('file not found')
            return url_for('books.list_books')

    # Some webpages, may have some special cases
    # if webpage_manager.additional_entries:
    #     data |= webpage_manager.additional_entries;

    data = webpage_manager.get_default_download_config_data()
    chapters = webpage_manager.get_book_chapters_list()

    # for key, value in data.items():
    #     data[key]["name"] = key
    #     data[key]["value"] = book_data.get(key)

    kwargs = {
    "TITLE": "Download Config",
    "DESCRIPTION": "",
    "SUBMIT": "Download",
    "DATA": data,
    "CHAPTERS": list(enumerate(chapters)),
    "NO_REDIRECT_ONSUBMIT": False,
    "INCLUDE_IMPORT_EXPORT": False,
    "ACTION": url_for('books.download_epub', id=id),
    }
    return render_template('download_config.html', **kwargs)
