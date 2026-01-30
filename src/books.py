from __future__ import annotations

import os
from datetime import datetime

import requests
from flask import Blueprint

blueprint = Blueprint("books", __name__)

import json

from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from ebooklib import epub
from flask import (
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

import src.book_data as bd
import src.user_data as user_data
from src.async_book_download import AsyncDownloadTask
from src.login import login_required
from src.webpages import match_url


@blueprint.route("/new_book", methods=["GET", "POST"])
@login_required
def new_book():
    if request.method == "POST":
        entry_point = request.form.get("entry_point")
        if entry_point is None:
            return redirect(url_for("home"))

        wm_class, match = match_url(entry_point)

        if wm_class is None:
            # TODO: HERE we can ask the user whether they want to make a custom web-crawler

            flash("Unknown Entry point url! Only RoyalRoad is supported at the moment")
            return redirect(url_for("home"))

        book_data_entries = wm_class.new_book_data(entry_point, match)
        bd.add_new_book_entry(wm_class.__name__, book_data_entries)

        flash("New book created successfully!")
        return redirect(url_for("home"))
    data = {
        "entry_point": {"label": "Starting URL", "value": ""},
    }
    kwargs = {
        "TITLE": "New Book",
        "DERCRIPTION": "",
        "SUBMIT": "Submit",
        "DATA": data,
        "ACTION": url_for("books.new_book"),
    }

    return render_template("forms/new_book.html", **kwargs)


@blueprint.route("/list_books", methods=["GET"])
@login_required
def list_books():
    query_tags = request.args.get("tags") or set()

    if isinstance(query_tags, str):
        query_tags = set([tag.strip() for tag in query_tags.split(",")])
        query_tags.discard("")

    books_list = []

    # USER_NAME2SUB: Make sure the kindle_address entry is also converted
    user_data.get_kindle_address()

    # Prepare the data list to pass to the template
    for book in bd.get_user_books():
        wm = book.get_wm()
        if wm is None:
            continue

        tags = set(book.get("tags") or [])

        if (
            # If 'all' is in the query_tags list, then show all entries
            query_tags.__contains__("all")
            or (  # If no query_tags then only show untaged entries
                len(query_tags) == 0 and len(tags) == 0
            )
            # or (  # If one of the entry tags is in the query;  OR policy
            #     len(tags.intersection(query_tags)) != 0
            # )
            or (  # If the entry has all the query_tags;  AND policy
                len(query_tags) != 0 and query_tags.issubset(tags)
            )
        ):
            books_list.append(
                {
                    "_id": wm.id,
                    "title": wm.get_book_data("title"),
                    "img_url": wm.get_book_data("cover_image"),
                    "tags": tags,
                }
            )

    return render_template(
        "books.html", data_list=books_list, ARCHIVE=query_tags.__contains__("archived")
    )


def get_tags(book: bd.BookData) -> set[str]:
    tags = book.get("tags") or []

    if not isinstance(tags, list):
        raise RuntimeError(
            f"Tags should be a set, got type: '{type(tags)}' value: '{str(tags)}'"
        )

    return set(tags)


def add_tags(book: bd.BookData, tags: set[str]):
    print("Adding tags", tags)

    book.set("tags", list(get_tags(book) | tags))


def remove_tags(book: bd.BookData, tags: set[str]):
    print("Removing ttags", tags)

    book.set("tags", list(get_tags(book) - tags))


@blueprint.route("unarchive_book/<id>", methods=["POST"])
@login_required
@bd.load_bookdata("id", "book")
def unarchive_book(id, book: bd.BookData):
    try:
        remove_tags(book, {"archived"})
    except Exception as e:
        print(e)
        return {"status": "error"}

    return {"status": "success"}


@blueprint.route("archive_book/<id>", methods=["POST"])
@login_required
@bd.load_bookdata("id", "book")
def archive_book(id, book: bd.BookData):
    print("Archiveing ", id)

    try:
        add_tags(book, {"archived"})
    except Exception as e:
        print(e)
        return {"status": "error"}

    return {"status": "success"}


@blueprint.route("download_config/<id>", methods=["GET", "POST"])
@login_required
@bd.load_bookdata("id", "book")
def download_config(id, book: bd.BookData):
    wm = book.get_wm()

    if request.method == "POST":
        config_data = wm.parse_download_config_data_form(request.form)
        do_send_to_kindle = request.form.get("do_send_to_kindle") == "true"
        downloadTask = AsyncDownloadTask.create_or_get(
            book, config_data, g.user.userinfo
        )

        downloadTask.do_send_to_kindle = do_send_to_kindle
        downloadTask.start_download()

        print("Status: ", downloadTask.status)
        print(downloadTask.status_msg())

        return downloadTask.status_msg()

    data = wm.get_default_download_config_data()
    chapters = wm.get_book_chapters_list()

    tags = book.get("tags") or []

    kwargs = {
        "BOOK_ID": id,
        "TITLE": "Download Config",
        "DESCRIPTION": "",
        "SUBMIT": "Download",
        "DATA": data,
        "CHAPTERS": list(enumerate(chapters))[::-1],
        "LAST_SEND_TO_KINDE": book.get("last_send_to_kindle", 0),
        "ARCHIVED": tags.__contains__("archived"),
    }
    return render_template("download_config.html", **kwargs)


@blueprint.route("download_epub_file/<download_id>", methods=["GET"])
def download_epub_file(download_id):
    task = AsyncDownloadTask.byID(download_id)
    # TODO: Could store the download_config as a file, when FINISHED,
    # So that the file may be accessible even when the task is removed from memory

    if task is None:
        responce = {
            "status": "ERROR",
            "error_code": 1,
            "error_msg": f"The download task '{download_id}' does not exit",
        }
        return json.dumps(responce)

    if task.status != task.FINISHED:
        return task.status_msg()

    if not os.path.exists(task.local_epub_filepath):
        responce = {
            "status": "ERROR",
            "error_code": 2,
            "error_msg": f"epub_file does not exists",
        }
        return json.dumps(responce)

    return send_file(
        task.local_epub_filepath,
        as_attachment=True,
        download_name="%s.epub" % task.download_config.get("title"),
    )


@blueprint.route("/delete_book/<id>", methods=["POST"])
@login_required
def delete_book(id):
    print("Deleting Book ", id)

    with bd.BookData(id) as book:
        if book.get("owner_sub") == g.user.user_sub:
            book.delete()
    return redirect(url_for("books.list_books"))


@blueprint.route("/download_status", methods=["POST"])
# @login_required
def download_status():
    download_id = request.json.get("download_id")

    task = AsyncDownloadTask.byID(download_id)
    if task is None:
        responce = {
            "status": "ERROR",
            "error_code": 1,
            "error_msg": f"The download task '{download_id}' does not exit",
        }
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
