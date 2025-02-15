
import os
import json
from datetime import datetime

import threading

import src.user_data as user_data
from .book_data import BookData
from .sendToKindle import sendToKindle

from flask import url_for

g_download_tasks = {}

class AsyncDownloadTask():
    FINISHED = "Finished"
    ERROR = "ERROR"
    DOWNLOADING = "Downloading"

    def __init__(self, _id: str, book: BookData,
                 download_config: dict, userinfo: dict):
        self.id = _id
        self.book = book
        self.download_config = download_config
        self.userinfo = userinfo

        self.local_epub_filepath = 'out/{}.epub'.format(self.id)
        self.download_url = url_for("books.download_epub_file", download_id=self.id)

        self.status = None
        self.percentage = 0.0
        self.do_send_to_kindle = False
        self.is_sent_to_kindle = False

        if os.path.exists(self.local_epub_filepath):
            self.status = AsyncDownloadTask.FINISHED

        # g_download_tasks[taskId] = self
        # self.status_file = 'status/{}.json'.format(datahash)

    @staticmethod
    def create_or_get(book: BookData, download_config: dict, userinfo: dict):
        wm = book.get_wm()
        datahash = wm.genereate_download_config_hash(download_config)

        # TODO: Using the datahash as an id is a bit odd. Unconventional at best
        #       and it might cause unforeseen problems.
        _id = datahash

        # global g_download_tasks
        if not g_download_tasks.__contains__(_id):
            task = AsyncDownloadTask(_id, book, download_config, userinfo)
            g_download_tasks[_id] = task
            return task
        else:
            return g_download_tasks.get(_id)

    @staticmethod
    def byID(_id: str):
        return g_download_tasks.get(_id)

    def status_msg(self):
        return json.dumps(self._status_msg_response())

    def start_download(self):
        if self.status is AsyncDownloadTask.ERROR:
            print("DEBUG: Task [{}] encountered an error!")
            return

        if self.status is AsyncDownloadTask.FINISHED:
            print("DEBUG: Task [{}] is already finished")
            if self.do_send_to_kindle and not self.is_sent_to_kindle:
                self.async_send_to_kindle()
            return

        if self.status is AsyncDownloadTask.DOWNLOADING:
            print("DEBUG: Task [{}] is already downloading")
            return

        self.status = AsyncDownloadTask.DOWNLOADING
        thread = threading.Thread(target = self._download_the_book)
        thread.start()

    def async_send_to_kindle(self):
        if self.is_sent_to_kindle:
            print("DEBUG: The book is already sent to the kindle")
            return

        if self.status is not AsyncDownloadTask.FINISHED:
            print("DEBUG: Task [{}] is not finished yet. Sending to kindle on finished")
            self.do_send_to_kindle = True

        thread = threading.Thread(target = self._send_to_kindle)
        thread.start()
        return


    def _status_msg_response(self):
        responce = {}
        responce["download_id"] = self.id

        if self.status is None:
            responce["status"] = "Undefined"
            return responce

        responce["status"] = self.status
        if self.status == AsyncDownloadTask.ERROR:
            responce["error_msg"]           = self.error_msg
        elif self.status == AsyncDownloadTask.FINISHED:
            responce["download_url"]        = self.download_url
        elif self.status == AsyncDownloadTask.DOWNLOADING:
            responce["percentage"] = "%u%s" % ( self.percentage, '%')

        return responce

    def _download_the_book(self):
        wm = self.book.get_wm()
        wm.download_book_to_server(self)
        try:
            wm.download_book_to_server(self)
        except Exception as e:
            self.status = AsyncDownloadTask.ERROR
            self.error_msg = str(e)
            print("ERRROR ", e.with_traceback)
            return

        if self.do_send_to_kindle:
            self._send_to_kindle()
        self.status = AsyncDownloadTask.FINISHED

    def _send_to_kindle(self):
        if self.is_sent_to_kindle:
            return

        self.is_sent_to_kindle = True
        self.book.set("last_send_to_kindle", int(datetime.now().timestamp()))
        self.book.push()
        user_sub = self.userinfo.get('sub')
        kindle_address = user_data.get_kindle_address(user_sub)
        if kindle_address is None:
            return

        title = self.download_config.get('title')
        print("DEBUG: Sending book {} ({})".format(title, self.id))

        sendToKindle(file = self.local_epub_filepath,
                target_filename="{}.epub".format(title),
                receiver = kindle_address)
        # NOTE: flash dose not work in task thread
        # flash('The email has been sent successfully')
