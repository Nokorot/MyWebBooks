
from .webpage_base import WebpageManager_Base
import src.download_manager as dm

from bs4 import BeautifulSoup

from urllib.parse import urljoin
import json, re
from datetime import datetime
# This file is intended to contain all the royalroad specific functionality
class RoyalRoadWM(WebpageManager_Base):
    download_config_entries =   {
        **WebpageManager_Base.download_config_entries,
        "include_authors_notes": {'label': 'Include Authors Notes', 'type': 'bool', 'value': False },
        "include_chapter_titles": {'label': 'Include Chapter Titles', 'type': 'bool', 'value': True },
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
        # TODO: The cache should not be ignored but timed out
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


    # TODO: These fixed default values should be defined in the dict above
    def get_default_book_include_images(self):
        return True

    def get_default_book_include_authors_notes(self):
        return False

    # TODO This should be advanced
    def get_default_book_include_chapter_titles(self):
        return True

    def get_book_chapters_list(self):
        chapters_table = self.get_fiction_page_bs().select('table#chapters')
        if len(chapters_table) < 1:
            return []

        result = []
        for row in chapters_table[0].find_all('tr'):
            # Find the first link in each row
            link = row.find('a')
            time = row.find('time')
            if time is None or link is None:
                continue

            dt = time.get('unixtime')

            if dt:
                dt = datetime.fromtimestamp(int(dt))
                # dt = str(dt)

            result.append((
               link.get_text().strip() if link else None,
               link['href'] if link else None,
               dt if time else None
            ))
        return result

    def download_book_to_server(self, task):
        self.init_epub(task.config_data)

        chapters = task.config_data.get('chapters')
        for index, url, title in chapters:
            chapter_url = urljoin(self.base_url, url)
            chapter_page_bs = dm.get_and_cache_html(chapter_url)

            chapter_content = []
            if task.config_data.get('include_chapter_titles', True):
                chapter_content.append('<h1>%s</h1>' % title)

            # if task.config_data.get('include_authors_notes', True):
            #     # This is a por solution, since only the first is added and always at the top
            #     note = chapter_page_bs.select('div.author-note-portle')[0]
            #      content.append(note)

            chapter_inner = chapter_page_bs.select('div.chapter-inner')[0]

            # Look for the style entry, which hides the "Stolen content" entry
            style_tags = chapter_page_bs.head.find_all('style')

            # Extract and analyze the content of each style tag
            for style_tag in style_tags:
                css_content = style_tag.get_text()
                # Use regular expressions to find the class name with display: none;
                match = re.search(r'\.(.*?)\s*{[^}]*display:\s*none;[^}]*}', css_content)
                if match:
                    hidden_class_name = match.group(1)
                    hidden_elements = chapter_inner.find_all(class_=hidden_class_name)
                    for element in hidden_elements:
                        element.extract()

            for img in chapter_inner.select('img'):
                if task.config_data.get('include_images', False):
                    epub_image_path = self.include_image(img.get('src'))
                    # TODO: Should down-scale imeages, to a more appropriate resolution
                    # imgobj = self.book.add_image(img.get('src'))
                    # imgobj.add_reference(self)

                    img['src'] = epub_image_path
                else:
                    img.drop_tree()

            # hr_url = task.config_data.get('replace_hr_box', "").strip()
            # if hr_url is not "":
            #     from bs4 import BeautifulSoup
            #     from bs4.builder import _lxml

            #     epub_image_path = self.include_image(hr_url)

            #     # String of HTML code for the <img> tag

            #     # NOTE: This could be user defined.
            #     img_html_code = """<div align="center" style="text-align:center; margin:1em">
            #                     <img src="{}" width="80%"/></div>""".format(epub_image_path)

            #     for hr in chapter_inner.select('hr'):
            #         # Create a new Tag object from the HTML code

            #         soup = BeautifulSoup(img_html_code, 'html.parser')
            #         img_tag = soup.find()
            #         # Tag(_lxml, 'img', None, True, img_html_code, True, None)

            #         hr.replace_with(img_tag)

            chapter_content.append(str(chapter_inner))

            self.add_chapter(title, "".join(chapter_content))

            task.percentage = 100*(index+1) // len(chapters)

        self.write_epub(task.local_epub_filepath)
