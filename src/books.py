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

@blueprint.route('/list_books',methods = ['GET'])
@login_required
def list_books():
    books_list = []

    # USER_NAME2SUB: Make sure the kindle_address entry is also converted
    user_data.get_kindle_address()

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
            book.delete()
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

        # TODO: Using the datahash as an id is a bit odd. Unconventional at best
        #       and it might cause unforeseen problems.
        global g_download_tasks
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
                book.set("last_send_to_kindle", int(datetime.now().timestamp()))

                send_file_to_kindle(task, user_kindle_address)
                task.is_sent_to_kindle = True

            book.close()  # This updates mongodb,
            # Need to do it manually, since this is on a different thread

            return task.status_msg()

        def download_the_book():
            task.status = task.DOWNLOADING
            task.percentage = 0

            wm.download_book_to_server(task)

            if do_send_to_kindle: #  and not task.is_sent_to_kindle:
                was_sendt, error_msg = send_file_to_kindle(task, user_kindle_address)

                book.set("last_send_to_kindle", int(datetime.now().timestamp()))

                if was_sendt:
                    task.is_sent_to_kindle = True
                book.close()

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
        "LAST_SEND_TO_KINDE": book.get("last_send_to_kindle", 0)
    }
    return render_template('download_config.html', **kwargs)
