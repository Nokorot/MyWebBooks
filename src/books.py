
import os
from datetime import datetime
import requests

from flask import Blueprint
blueprint= Blueprint("books", __name__)

from bs4 import BeautifulSoup
from flask import render_template, request, url_for, redirect, g, session, flash, send_file
from bson.objectid import ObjectId
from ebooklib import epub

from src.login import login_required

import src.user_data as user_data
import src.book_data as bd

from src.webpages import match_url

from src.async_book_download import AsyncDownloadTask

import json

@blueprint.route('/new_book',methods=['GET', 'POST'])
@login_required
def new_book():
    if request.method == 'POST':
        entry_point = request.form.get('entry_point')
        if entry_point is None:
            return redirect(url_for('home'))

        wm_class, match = match_url(entry_point)

        if wm_class is None:
            # TODO: HERE we can ask the user whether they want to make a custom web-crawler

            flash("Unknown Entry point url! Only RoyalRoad is supported at the moment")
            return redirect(url_for('home'))

        book_data_entries = wm_class.new_book_data( entry_point, match )
        bd.add_new_book_entry(wm_class.__name__, book_data_entries)

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

    # Prepare the data list to pass to the template
    for book in bd.get_user_books():
        wm = book.get_wm()
        if wm is None:
            continue

        books_list.append({
            '_id':     wm.id,
            'title':   wm.get_book_data('title'),
            'img_url': wm.get_book_data('cover_image')
        })

    return render_template('books.html', data_list=books_list)

@blueprint.route('download_config/<id>',methods=['GET', 'POST'])
@login_required
@bd.load_bookdata('id', 'book')
def download_config(id, book):
    wm = book.get_wm()

    if request.method == 'POST':
        config_data = wm.parse_download_config_data_form(request.form)
        do_send_to_kindle = request.form.get("do_send_to_kindle") == 'true'
        
        downloadTask = AsyncDownloadTask.create_or_get( \
                book, config_data, g.userinfo)

        downloadTask.do_send_to_kindle = do_send_to_kindle
        downloadTask.start_download()

        print("Status: ", downloadTask.status)
        print(downloadTask.status_msg())

        return downloadTask.status_msg()

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

@blueprint.route('download_epub_file/<download_id>',methods=['GET'])
def download_epub_file(download_id):
    task = AsyncDownloadTask.byID(download_id)
    # TODO: Could store the download_config as a file, when FINISHED, 
    # So that the file may be accessible even when the task is removed from memory

    if task is None:
        responce = {
            'status': 'ERROR', 
            'error_code': 1, 
            'error_msg': f"The download task '{download_id}' does not exit" }
        return json.dumps(responce)

    if task.status != task.FINISHED:
        return task.status_msg()

    if (not os.path.exists(task.local_epub_filepath)):
        responce = {
            'status': 'ERROR', 
            'error_code': 2, 
            'error_msg': f"epub_file does not exists" }
        return json.dumps(responce)

    return send_file(task.local_epub_filepath, as_attachment = True, \
        download_name="%s.epub" % task.download_config.get('title'))


@blueprint.route('/delete_book/<id>')
@login_required
def delete_book(id):
    with bd.BookData(id) as book:
        if book['owner'] == g.user['userinfo']['name']:
            book.delete()
    return redirect(url_for('books.list_books'))

@blueprint.route('/download_status',methods=['POST'])
# @login_required
def download_status():
    download_id = request.json.get('download_id')

    task = AsyncDownloadTask.byID(download_id)
    if task is None:
        responce = {
            'status': 'ERROR', 
            'error_code': 1, 
            'error_msg': f"The download task '{download_id}' does not exit" }
        return json.dumps(responce)

    return task.status_msg()



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

