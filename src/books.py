from datetime import datetime
import requests

from flask import Blueprint
blueprint= Blueprint("books", __name__)

from bs4 import BeautifulSoup
from flask import render_template, request, url_for, redirect, g, session, flash, send_file, send_file
from bson.objectid import ObjectId
from ebooklib import epub

import os
import src.mongodb_api_1 as mongodb_api
from src.login import login_required

import src.user_data as user_data
from src.book_data import BookData, load_bookdata

import json

@blueprint.route('/new_book',methods=['GET', 'POST'])
@login_required
def new_book():
    if request.method == 'POST':
        entry_point = request.form.get('entry_point')
        if entry_point is None:
            return redirect(url_for('home'))

        from src.webpages import match_url
        wm_class, match = match_url(entry_point)

        if wm_class is None:
            # TODO: HERE we can ask the user whether they want to make a custom web-crawler

            flash("Unknown Entry point url! Only RoyalRoad is supported at the moment")
            return redirect(url_for('home'))

        book_data_entries = wm_class.new_book_data( entry_point, match )
        mongodb_api.insertOne('rr', 'books', {
            'owner' : g.user['userinfo']['name'],
            'wm_class_name': wm_class.__name__,
            **book_data_entries,
            })

        flash('New book created successfully!')
        return redirect(url_for('home'))
    data = {
        "entry_point": {
            'label': "Starting URL",
            'value': "" },
    }
    kwargs = {
        "TITLE": "New Book",
        "DERCRIPTION": "",
        "SUBMIT": "Submit",
        "DATA": data,
        "ACTION": url_for('books.new_book'),
    }

    return render_template('forms/new_book.html', **kwargs)


@blueprint.route('/edit_book/<id>',methods=['GET', 'POST'])
@login_required
@load_bookdata('id', 'book')
def edit_book(id, book):
    if not book.is_owner(g.user['userinfo']['name']):
        redirect(url_for('books.list_books'))

    wm = book.get_wm()

    if request.method == 'POST':
        # TODO: This is severely outdated, should use the wm_class object

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

        mongodb_api.updateOne('rr','books', {'_id': ObjectId(id)}, book_form_template)
        flash("data updated!")
        return 'Data updated successfully.'

    # data = {
    #     "title": {'label': "Title"},
    #     "author": {'label': "author"},
    #     "cover_image": {'label': "Cover Image URL"},
    #     "entry_point": {'label': "Starting URL", 'value': "royalroad.com" },
    #     "rss": {'label': "RSS URL", 'value': "" },
    #     "section_css_selector": {'label': "Section CSS selector", 'value': "" },
    #     "title_css_selector": {'label': "Title CSS selector", 'value': "" },
    #     "paragraph_css_selector": {'label': "Paragraph CSS selector",'value': "" },
    #     "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'value': "" }
    # }
    # for key, value in data.items():
    #     data[key]["value"] = book[key]

    entries = wm.get_config_entries()
    from pprint import pprint
    pprint(entries)

    kwargs = {
        "TITLE": "Edit Data",
        "DERCRIPTION": "",
        # "SUBMIT": "Save",
        "DATA": entries,
        # "NO_REDIRECT_ONSUBMIT": True,
        # "INCLUDE_IMPORT_EXPORT": True,
        "ACTION": url_for('books.edit_book', id=id),
    }
    return render_template('edit_book.html', **kwargs)

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

@blueprint.route('/list_books',methods = ['GET'])
@login_required
def list_books():
    books_list = []

    from src.book_data import get_user_books
    # Prepare the data list to pass to the template
    for book in get_user_books():
        wm = book.get_wm()
        if wm is None:
            continue

        books_list.append({
            '_id':     wm.id,
            'title':   wm.get_book_data('title'),
            'img_url': wm.get_book_data('cover_image')
        })

    return render_template('books.html', data_list=books_list)

@blueprint.route('/delete_book/<id>')
@login_required
def delete_book(id):
    with BookData(id) as book:
        if book['owner'] == g.user['userinfo']['name']:
            book.delete();
    return redirect(url_for('books.list_books'))

@blueprint.route('download_status',methods=['POST'])
# @login_required
def download_status():
    download_id = request.json.get('download_id')

    if download_id is None:
        return "{'status': 'ERROR', 'error_code': 1, 'error_msg': 'download_id was not given'}"

    task = DownloadTask.byID(download_id)
    return task.status_msg()

def send_file_to_kindle(task, user_kindle_address=None):
    from .sendToKindle import sendToKindle
    if user_kindle_address is None:
        user_kindle_address = user_data.get_kindle_address()
    if not user_kindle_address:
        flash('The kindle email address was not set. Please enter and submit your kindle email address')
        return False, {'status': 'ERROR', 'error_code': 4, 'error_msg': 'The kindle_address was not set'}

    # print("HEYY ", current_app)
    # TODO:
    # current_app is not defined in the task thread
    # if current_app.config['DEBUG'] == True:
    #     print("DEBUG: Skipping sending file to kindle in debug mode")
    # else:
    #     pass

    if True:
        title = task.config_data.get('title')
        sendToKindle(file = task.local_epub_filepath,
                target_filename="{}.epub".format(title),
                receiver = user_kindle_address)

    # NOTE: flash dose not work in task thread
    # flash('The email has been sent successfully')

    return True, None

# UNUSED:
# @blueprint.route('send_epub_file_to_kindle',methods=['POST'])
# def send_epub_file_to_kindle():
#     download_id = request.json.get('download_id')
#     if download_id is None:
#         return "{'status': 'ERROR', 'error_code': 1, 'error_msg': 'download_id was not given'}"
#     local_epub_filepath = 'out/{}.epub'.format(download_id)
#     if (not os.path.exists(local_epub_filepath)):
#         return "{'status': 'ERROR', 'error_code': 2, 'error_msg': 'epub_file does not exists'}"
#
#     download_config_file = 'out/config_{}.json'.format(download_id)
#     if (not os.path.exists(download_config_file)):
#         return "{'status': 'ERROR', 'error_code': 3, 'error_msg': 'download_config_file does not exists'}"
#
#     with open(download_config_file, 'r') as f:
#         config_data = json.load(f)
#
#     return send_file_to_kindle(local_epub_filepath, config_data);

@blueprint.route('download_epub_file/<download_id>',methods=['GET'])
def download_epub_file(download_id):
    task = DownloadTask.byID(download_id)

    if task.status != task.FINISHED:
        return task.status_msg()

    if (not os.path.exists(task.local_epub_filepath)):
        return "{'status': 'ERROR', 'error_code': 2, 'error_msg': 'epub_file does not exists'}"

    return send_file(task.local_epub_filepath, as_attachment = True, \
        download_name="%s.epub" % task.config_data.get('title'))


g_download_tasks = {}
class DownloadTask():
    FINISHED = "Finished"
    DOWNLOADING = "Downloading"

    def __init__(self, taskId):
        self.id = taskId
        self.is_sent_to_kindle = False
        self.status = None

        g_download_tasks[taskId] = self
        # self.status_file = 'status/{}.json'.format(datahash)

    @staticmethod
    def byID(taskId):
        global g_download_tasks
        task = g_download_tasks.get(taskId)
        if task is None:
            task = DownloadTask(taskId)
        return task

    def _status_msg_response(task):
        responce = {}
        if task.status is not None:
            responce["status"] = "Undefined"
            return responce

        responce["status"] = task.status
        if task.status == task.FINISHED:
            responce["download_url"]        = task.download_url
            responce["download_id"]         = task.download_id
        elif task.status == task.DOWNLOADING:
            responce["percentage"] = "%u%s" % ( task.percentage or 0, '%')

        return responce

    def status_msg(self):
        return json.dumps(self._status_msg_response())

    def set(self, key, value):
        self.status.set(key, value)

    def get(self, key, default=None):
        self.status.get(key, default)

@blueprint.route('download_config/<id>',methods=['GET', 'POST'])
@login_required
@load_bookdata('id', 'book')
def download_config(id, book):
    wm = book.get_wm()

    if request.method == 'POST':
        config_data = wm.parse_download_config_data_form(request.form)
        datahash    = wm.genereate_download_config_hash(config_data)
        do_send_to_kindle = request.form.get("do_send_to_kindle") == 'true'

        user_kindle_address = user_data.get_kindle_address()

        global g_download_tasks
        print(g_download_tasks, datahash)

        if not g_download_tasks.__contains__(datahash):
            task = DownloadTask(datahash)
            task.config_data = config_data
            task.local_epub_filepath = 'out/{}.epub'.format(task.id)
            task.download_url = url_for("books.download_epub_file", download_id=task.id)
            if os.path.exists(task.local_epub_filepath):
                task.status = task.FINISHED
        else:
            task = g_download_tasks.get(datahash)
            if task.status == task.DOWNLOADING:
                return task.status_msg()

        if task.status == task.FINISHED:
            print("DEBUG: Already exists")
            # is_sent_to_kindle most be user spesific
            if do_send_to_kindle: # and not task.is_sent_to_kindle:
                send_file_to_kindle(task, user_kindle_address)
                task.is_sent_to_kindle = True

            return task.status_msg()

        def download_the_book():
            task.status = task.DOWNLOADING
            task.percentage = 0

            wm.download_book_to_server(task)

            if do_send_to_kindle: #  and not task.is_sent_to_kindle:
                was_sendt, error_msg = send_file_to_kindle(task, user_kindle_address)

                if was_sendt:
                    task.is_sent_to_kindle = True

            task.status = task.FINISHED

        import threading
        thread = threading.Thread(target = download_the_book)
        thread.start()
        # download_the_book()

        return datahash

    data = wm.get_default_download_config_data()
    chapters = wm.get_book_chapters_list()

    kwargs = {
        "TITLE": "Download Config",
        "DESCRIPTION": "",
        "SUBMIT": "Download",
        "DATA": data,
        "CHAPTERS": list(enumerate(chapters))[::-1],
    }
    return render_template('download_config.html', **kwargs)
