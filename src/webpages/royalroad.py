
from src.webpages.webpage_base import WebpageManager_Base
import src.download_manager as dm

from urllib.parse import urljoin

# This file is intended to contain all the royalroad specific functionality

class RoyalRoad(WebpageManager_Base):
    download_config_enrtires = WebpageManager_Base.download_config_enrtires | {
        "include_authors_notes": {'label': 'Include Authors Notes', 'type': 'bool', 'value': False },
    }

    base_url = 'https://www.royalroad.com'

    def __init__(self,id, book):
        WebpageManager_Base.__init__(self, id, book)

    def get_fiction_page_bs(self):
        if hasattr(self, 'fiction_page_bs'):
            return self.fiction_page_bs
        
        fiction_page_url = self.book.get('entry_point')
        self.fiction_page_bs = dm.get_html(fiction_page_url, ignore_cache=True)
        return self.fiction_page_bs
    
    def get_default_book_title(self):
        return self.get_fiction_page_bs().select_one('div.fic-title h1').text
    
    def get_default_book_author(self):
        return self.get_fiction_page_bs().select_one('div.fic-title a').text
    
    def get_default_book_language(self):
        return "en"
    
    def get_default_book_cover_image(self):
        return self.get_fiction_page_bs().select_one('img.thumbnail').get('src')
    
    def get_default_book_include_images(self):
        return True
    
    def get_default_book_include_authors_notes(self):
        return False
    
    def get_book_chapters_list(self):
        chapters_table = self.get_fiction_page_bs().select('table#chapters')
    
        first_column_data = []
        for row in chapters_table[0].find_all('tr'):
            # Find the first link in each row
            link = row.find('a')
            
            if link and 'href' in link.attrs:
                first_column_data.append((link.get_text().strip(), link['href']))
    
        return first_column_data
    
    def download_book_to_server(self, config_data, local_epub_filepath):
        self.init_epub(config_data)

        for index, url, title in config_data.get('chapters'):
            chapter_url = urljoin(self.base_url, url)
            chapter_page_bs = dm.get_and_cache_html(chapter_url)

            # TODO: This needs some work! For example, there is no images and no tables
            content = str(chapter_page_bs.select('div.chapter-inner'))
            self.add_chapter(title, content)
    
        self.write_epub(local_epub_filepath)
