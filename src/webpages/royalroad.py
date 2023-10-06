
import requests
from bs4 import BeautifulSoup 
from src.webpages.webpage_base import WebpageManager_Base

from ebooklib import epub

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
        fiction_page = requests.get(fiction_page_url).text
        self.fiction_page_bs = BeautifulSoup(fiction_page, features="lxml")
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
    
    
    def download_book(self, config_data, local_epub_filepath):
        #if already in server
        # if(os.path.exists(local_ebook_filepath)):
        #     return local_ebook_filepath
    
        ebook = epub.EpubBook()
        # mandatory metadata
        ebook.set_identifier(self.id)
        ebook.set_title(config_data.get('title'))
        ebook.set_language(config_data.get('language'))
        ebook.add_author(config_data.get('author'))
        #collect chapters

        from urllib.parse import urljoin

        for index, url, text in config_data.get('chapters'):
            print(f'downloading chapter {index}')
            chapter_url = urljoin(self.base_url, url)
            print(chapter_url)

            chapter_page = requests.get(chapter_url).text
            chapter_page_bs = BeautifulSoup(chapter_page, features="lxml")

            temp_chapter = epub.EpubHtml(title = text,
                                         file_name = f'chapter_{index}.xhtml')

            # TODO: This needs some work! For example, there is no images and no tables
            temp_chapter.set_content( 
                    str(chapter_page_bs.select('div.chapter-inner'))
                # str(chapter_page_bs.select_one('h1')) +
                # ''.join([str(x) for x in chapter_page_bs.select('div.chapter-content p')])
            )
            ebook.add_item(temp_chapter)
            ebook.toc.append(temp_chapter)
            ebook.spine.append(temp_chapter)
    
        print('chapters packed')
        ebook.add_item(epub.EpubNcx())
        ebook.add_item(epub.EpubNav())
        epub.write_epub(local_epub_filepath, ebook)
        print('book in the server')
