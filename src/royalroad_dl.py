
from flask import Blueprint, render_template, request, url_for, send_file
blueprint = Blueprint('royalroad_dl', __name__)


from htmlmin import minify

# TODO: Make this a cron job
@blueprint.route("/download-book", methods=['POST'])
def download_book():  
    def gen_config(data):
        url_hash="TEST"

        # FOLDERNAME = hash_url
        config = {}
        config['cache'] = f'cache/{url_hash}'
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
    config.ignore_last_cache = True

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
    import os
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
        "OUTFILE"    : {'label': 'Epub File Name', },
    }

    if request.method == 'POST':
        request_data = request.form

        fiction_page_url = request_data.get("fiction_page_url");

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
            "ACTION": url_for("royalroad_dl.download_book"),
    }
    return render_template('data_form.html', **kwargs)
