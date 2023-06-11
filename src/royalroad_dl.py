
from flask import Blueprint, render_template, request, url_for, send_file, redirect
blueprint = Blueprint('royalroad_dl', __name__)


from htmlmin import minify


@blueprint.route("/download-bookfile/<id>", methods=['GET', 'POST'])
def download_book_submit(id):
    if request.method == 'POST':
        filename = request.form.get('epub_filename', f"{id}.epub")
        action = request.form.get('action')

        print(request.form)

        if action == 'Download':
            return send_file(f'out/{id}.epub', download_name=filename)
        elif action == 'SendToKindle':
            from src.sendToKindle import main as sendToKindle

            kindle_email = request.form.get("kindle_email")
            # TODO: Some error message if missing
    
            print(f"Sending To Kindle, email: {kindle_email},  epub: {filename}")
            sendToKindle(f'out/{id}.epub', receiver=kindle_email, target_filename=filename)

        return f"Unknown action! {action}"

    epub_filename = request.args.get('epub_filename', f"{id}.epub")
    data = {
        "epub_filename": {'label': "Epub File Name", 'text': epub_filename},
        "kindle_email": {'label': "Kindle Email"}, # NOTE: This key is referred to in the html
    }


    sentders_email="torhoaakon@gmail.com"

    kwargs = {
            "TITLE": "Download Succeeded!",
            "BOOK_ID": id,
            "ACTION": url_for("royalroad_dl.download_book_submit", id=id),
            "DATA": data,
            "SENDERS_EMAIL": sentders_email,
    }

    return render_template("dowanload_success.html", **kwargs)




# TODO: Make this a cron job
@blueprint.route("/download-book/<id>", methods=['POST'])
def download_book(id):  
    def gen_config(id, data):
        # FOLDERNAME = hash_url
        config = {}
        config['cache'] = f'cache/{id}'
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
            "epub_filename": f'out/{id}.epub',
            # "epub_filename": 'out/' + data["OUTFILE"],
            "cover_image": data["COVER"],
            "css_filename": "webbook_dl/kindle.css",
            "entry_point": data["ENTRY"],
            "chapter": css_selectors,
            "include_images": data.get("INCLUDE_IMG", False),
        }

        config['book'] = book 
        return config

    # Could be some hash perhaps


    from html_to_epub import Config, Book
    config = Config(gen_config(id, request.form))
    config.ignore_last_cache = True

    import os
    os.makedirs(config.cache, exist_ok=True)

    # # Note: This looks very relative
    # klass = get_callback_class(config.callbacks)
    # book = Book(config, klass(config))
    
    # Still relative
    from books.RR_Template.cbs_base import Callbacks
    book = Book(config, Callbacks(config))

    book.load_html()

    print(config.book.epub_filename)

    from ebooklib import epub
    epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
 

    from RR_cnf_gen import foldername_from_title
    epub_filename = "%s.epub" % foldername_from_title(book.title)


    return redirect(url_for("royalroad_dl.download_book_submit", id=id, epub_filename=epub_filename))

    return render_template("dowanload_success.html", **kwargs)

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
