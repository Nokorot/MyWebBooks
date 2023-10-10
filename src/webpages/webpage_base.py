from ebooklib import epub
import src.download_manager as dm

import re

class WebpageManager_Base():
    download_config_enrtires = {
        "title": {'label': "Title"},
        "author": {'label': "author"},
        "language": {'label': "Language"},
        "cover_image": {'label': "Cover Image URL"},
        "include_images"  : {'label': 'Include Images', 'type': 'bool' },
        # TODO: "epub_filename": {'label': "Cover Image URL"},
     }

    default_kindle_css = "./data/kindle.css"

    url_pattern = None

    def __init__(self, id, book):
        self.id = id
        self.book = book;

    @classmethod
    def match_url(cls, url):
        if cls.url_pattern is None:
            return None
        return re.match(cls.url_pattern, url)

    def get_book_data(self, key):
        value = self.book.get(key)
        if not value is None:
            return value
        default_method = getattr(self, 'get_default_book_%s' % key)
        if not default_method is None:
            return default_method()
        return None

    # This function is meant to retrieve information like title, author and chapteres available from the books coverpage, that is the 'fiction page' in the case of royalroad
    def get_default_download_config_data(self):
        data = {}
        # book_data = webpage_manager.get_book_data(book)

        for key, value in self.download_config_enrtires.items():
            data[key] = value.copy() | \
                    { 'value': getattr(self, 'get_default_book_%s' % key)() };
        return data

    def genereate_download_config_hash(self, download_config_data):
        from hashlib import sha256
        import json, base64

        shahash = sha256(json.dumps(download_config_data).encode('utf-8'))
        return base64.b64encode(shahash.digest()).decode().replace('/','_')

    def parse_download_config_data_form(self, form_data):
        download_config_data = {}
        for key in self.download_config_enrtires.keys():
            if not key in form_data:
                download_config_data[key] = getattr(self, 'get_default_book_%s' % key)()
            elif self.download_config_enrtires[key].get("type") == 'bool':
                # This is a work around, since an unchecked checkbox is simply not included in the form_data
                download_config_data[key] = '1' in form_data.getlist(key)
            else:
                download_config_data[key] = form_data.get(key)

        chapters = []
        for key, value in form_data.items():
            if key.startswith('chapter-cbx'):
                index = int(key[len('chapter-cbx-'):])
                url = form_data.get('chapter-url-%u' % index)
                text = form_data.get('chapter-text-%u' % index)
                chapters.append((index, url, text))

        download_config_data['chapters'] = sorted(chapters, key=lambda x: x[0])
        return download_config_data

    def init_epub(self, config_data):
        self.ebook = epub.EpubBook()
        # mandatory metadata
        self.ebook.set_identifier(self.id)
        self.ebook.set_title(config_data.get('title'))
        self.ebook.set_language(config_data.get('language'))
        self.ebook.add_author(config_data.get('author'))

        with open(self.default_kindle_css, 'r') as f:
            css = epub.EpubItem(uid='default', file_name="style/kindle.css", \
                    media_type="text/css", content=f.read())
            self.ebook.add_item(css)

        cover_img_url = config_data.get('cover_image')
        if cover_img_url:
            cover_img_data = dm.get_and_cache_image_data(cover_img_url)
            self.ebook.set_cover("cover.png", cover_img_data)

        self.chapter_count = 0;

    def add_chapter(self, title, contnet): # add_images_in_content=True)
        self.chapter_count += 1;
        chapter = epub.EpubHtml(title = title,
                    file_name = f'chapter_{self.chapter_count}.xhtml')
        chapter.set_content(contnet)
        self.ebook.add_item(chapter)
        self.ebook.toc.append(chapter)
        self.ebook.spine.append(chapter)

    def write_epub(self, local_epub_filepath):
        self.ebook.add_item(epub.EpubNcx())
        self.ebook.add_item(epub.EpubNav())
        epub.write_epub(local_epub_filepath,self.ebook)
