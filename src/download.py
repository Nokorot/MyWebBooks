from ebooklib import epub
from flask import redirect, url_for, request

from .books import blueprint 

class EBook():
    def __init__():
        title = title 

@blueprint.route('download_epub')
def download_epub():
    ebook = epub.EpubBook()
    print(request.form)
    return redirect(url_for('books.list_books'))
