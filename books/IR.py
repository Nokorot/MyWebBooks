
import lxml.html
from html_to_epub.lib.callbacks import Callbacks

class Callbacks(Callbacks):

    def __init__(self, config):
        self.config = config
        self.sections = dict()

    def chapter_title_callback(self, selector_matches):
        return selector_matches[0].text

    def chapter_text_callback(self, selector_match):
        # This removes the Title that is part of the content on the webpage
        selector_match.cssselect('p')[0].drop_tree()

        for table in selector_match.cssselect('table'):
            table.set('style', None)

        for td in selector_match.cssselect('td'):
            td.set('style', "border: solid 1px; width: 50%;")

        for hr in selector_match.cssselect('hr'):
            img = lxml.html.fromstring('<div align="center"><img src="images/sep.png" width=80%></div>')
            hr.getparent().replace(hr, img)
        return selector_match
