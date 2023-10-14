
from .webpage_base import WebpageManager_Base
import src.download_manager as dm

from urllib.parse import urljoin
import json

# This file is intended to contain all the royalroad specific functionality
class RoyalRoadWM(WebpageManager_Base):
    download_config_enrtires =   {
        **WebpageManager_Base.download_config_enrtires,
        "include_authors_notes": {'label': 'Include Authors Notes', 'type': 'bool', 'value': False },
    }

    base_url = 'https://www.royalroad.com'
    url_pattern = '^(https?://)?(www\.)?royalroad\.com/fiction/(?P<id>[\d]+)(/.*)?$'

    def __init__(self,id,book):
        WebpageManager_Base.__init__(self, id, book)

    @classmethod
    def new_book_data(cls, entry_point, match):
        fiction_page_url = cls.base_url + '/fiction/' + match.group('id')
        return { 'fiction_page': fiction_page_url };

    def get_fiction_page_bs(self):
        if hasattr(self, 'fiction_page_bs'):
            return self.fiction_page_bs

        fiction_page_url = self.book.get('fiction_page') or self.book.get('entry_point')
        self.fiction_page_bs = dm.get_html(fiction_page_url, ignore_cache=True)
        return self.fiction_page_bs

    def get_default_book_title(self):
        return self.get_fiction_page_bs().select_one('div.fic-title h1').text

    def get_default_book_author(self):
        return self.get_fiction_page_bs().select_one('div.fic-title a').text

    def get_default_book_language(self):
        return "en"

    def get_default_book_cover_image(self):
        cover_img_url = self.get_fiction_page_bs().select_one('img.thumbnail').get('src')
        return  urljoin(self.base_url, cover_img_url)

    def get_default_book_include_images(self):
        return True

    def get_default_book_include_authors_notes(self):
        return False

    def get_book_chapters_list(self):
        chapters_table = self.get_fiction_page_bs().select('table#chapters')
        if len(chapters_table) < 1:
            return []

        first_column_data = []

        for row in chapters_table[0].find_all('tr'):
            # Find the first link in each row
            link = row.find('a')

            if link and 'href' in link.attrs:
                first_column_data.append((link.get_text().strip(), link['href']))

        return first_column_data

    def download_book_to_server(self, config_data, local_epub_filepath, status_file):
        self.init_epub(config_data)

        chapters = config_data.get('chapters')
        for index, url, title in chapters:
            chapter_url = urljoin(self.base_url, url)
            chapter_page_bs = dm.get_and_cache_html(chapter_url)

            content = chapter_page_bs.select('div.chapter-inner')[0]

            for img in content.select('img'):
                if config_data.get('include_images', False):
                    epub_image_path = self.include_image(img.get('src'))
                    # TODO: Should down-scale imeages, to a more appropriate resolution
                    # imgobj = self.book.add_image(img.get('src'))
                    # imgobj.add_reference(self)
                    
                    print(epub_image_path)
                    print(img)
                    img['src'] = epub_image_path
                else:
                    img.drop_tree()

            # TODO: This needs some work! For example, there is no images and no tables
            self.add_chapter(title, content)

            status = {
                    "status": "Downloading", 
                    "percentage": "%u%s" % ( 100*(index+1) // len(chapters), '%')
                    # "download_url": download_url
            } 
            with open(status_file, 'w') as f:
                f.write(json.dumps(status));

        self.write_epub(local_epub_filepath)
