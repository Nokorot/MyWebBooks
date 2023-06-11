
from flask import Blueprint, render_template, request, url_for, send_file
blueprint = Blueprint('royalroad_dl', __name__)


from htmlmin import minify

"""
cache: './cache/html/<+FOLDERNAME+>'
callbacks: 'books.<+FOLDERNAME+>.cbs.Callbacks'
book:
    title: <+TITLE+> 
    author: <+AUTHOR+> 
    epub_filename: out/<+FOLDERNAME+>.epub
    cover_image: <+COVER_IMAGE+>
    css_filename: 'kindle.css'
    entry_point: <+ENTRY_POINT+>
    chapter:
        section_css_selector: 'div.fic-header h1.font-white'
        title_css_selector: 'div.fic-header h1.font-white'
        text_css_selector: 'div.chapter-inner'
        next_chapter_css_selector: 'div.col-md-offset-4 a.btn'
    include_images: True
"""


@blueprint.route("/download-book", methods=['POST'])
def download_book():
    def gen_config(data):
        url_hash="TEST"

        # FOLDERNAME = hash_url
        config = {}
        config['cache'] = 'cache/{url_hash}'
        config['ignore_cache'] = False # data.get('ignore_cache', True)

        # config['callbacks'] = "books.RR_Template.cbs_base"

        css_selectors = {
            "section_css_selector": 'div.fic-header h1.font-white',
            "title_css_selector": 'div.fic-header h1.font-white',
            "text_css_selector": 'div.chapter-inner',
            "next_chapter_css_selector": 'div.col-md-offset-4 a.btn'
        }

        book = { 
            "title": data["TITLE"],
            "author": data["AUTHOR"],
            "epub_filename": 'out/' + data["OUTFILE"],
            "cover_image": data["COVER"],
            "css_filename": "webbook_dl/kindle.css",
            "entry_point": data["ENTRY"],
            "chapter": css_selectors,
        }

        config['book'] = book 
        return config


    from html_to_epub import Config, Book
    config = Config(gen_config(request.form))

    import os
    os.makedirs(config.cache, exist_ok=True)

    # # Note: This looks very relative
    # klass = get_callback_class(config.callbacks)
    # book = Book(config, klass(config))
    
    # Still relative
    from books.RR_Template.cbs_base import Callbacks
    book = Book(config, Callbacks(config))

    print(config)

    book.load_html()

    print(config.book.epub_filename)

    from ebooklib import epub
    epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
    
    return send_file(config.book.epub_filename)


@blueprint.route("/", methods=['GET', 'POST'])
def head():
    kwargs = {
            "TITLE": "RoyalRoad Book Download",
            "DERCRIPTION": "Enter the url to the fiction page of a royalroad book",
            "SUBMIT": "Submit",
            "DATA": {'url': {'label': 'Url', 'type': 'str', 'text': ''}},
            "ACTION": url_for("royalroad_dl.book_config"),
    }
    return render_template('data_form.html', **kwargs)


@blueprint.route("/configure-book", methods=['GET', 'POST'])
def book_config():
    data = {
        "TITLE"      : {'label': 'Title',          },
        "AUTHOR"     : {'label': 'Author',         },
        "COVER"      : {'label': 'Cover',          },
        "ENTRY"      : {'label': 'First Chapeter', },
        "OUTFILE"    : {'label': 'Epub File Name', },
    }

    if request.method == 'POST':
        for key in data.keys():
            data[key]['text'] = request.form.get(key)

    kwargs = {
            "TITLE": "RoyalRoad Book Configuration",
            "DERCRIPTION": "Please check that the following configuration is correct",
            "SUBMIT": "Download",
            "DATA": data,
            "NO_REDIRECT_ONSUBMIT": False,
            # "ACTION": url_for("royalroad_dl.book_config"),
            "ACTION": url_for("royalroad_dl.download_book"),
    }
    return render_template('data_form.html', **kwargs)
