import yaml, logging, sys

_MAX_CHAPTER_ITERATIONS = 7000


class ChapterConfig:
    def __init__(self, yml):
        self.title_css_selector = yml.get('title_css_selector')
        self.text_css_selector = yml['text_css_selector']
        self.section_css_selector = yml.get('section_css_selector')
        self.next_chapter_css_selector = yml['next_chapter_css_selector']

    def __str__(self):
        return "    Chapter{{\n      title_css_selector: '{}'\n      text_css_selector: '{}'\n      section_css_selector: '{}'\n      next_chapter_css_selector: '{}'\n    }}".format(self.title_css_selector, self.text_css_selector, self.section_css_selector, self.next_chapter_css_selector)

class BookConfig:
    def __init__(self, yml):
        self.title = yml['title']
        self.author = yml['author']
        self.epub_filename = yml['epub_filename']
        self.chapter = ChapterConfig(yml['chapter'])
        self.css_filename = yml['css_filename']
        self.entry_point = yml['entry_point']

        print(yml)
        self.cover_img = yml.get('cover_image', None)

        self.images = yml.get('images', {})

    def __str__(self):
        return "  Book{{\n    title: '{}'\n    author: '{}'\n    epub_filename: '{}'\n    css_filename: '{}'\n    entry_point: '{}'\n{}\n  }}".format(self.title, self.author, self.epub_filename, self.css_filename, self.entry_point, str(self.chapter))

class Config:
    def __init__(self, configData, debug=False, toc_break=False):
        if isinstance(configData, dict):
            config = configData
        elif isinstance(configData, str):
            logging.getLogger().debug('Loading yaml config ' + configData)
            with open(configData, 'r') as ymlfile:
                config = yaml.safe_load(ymlfile)
        else:
            raise ValueError("'configData' most be a 'dict' or a 'str', got '%s'" % type(configData))

        self.book = BookConfig(config['book'])
        self.cache = config['cache']
        self.ignore_cache = config.get('ignore_cache', False)

        self.callbacks = config.get('callbacks', None)
        self.max_chapter_iterations = \
                config.get('max_chapter_iterations', _MAX_CHAPTER_ITERATIONS)

        self.images_dir = config.get('images_dir', 'images/')

        self.custom = config.get('custom', {})

        self.debug = debug
        self.toc_break = toc_break

    def __str__(self):
        return "\nConfig{{\n  cache: '{}'\n  html_callbacks: {}\n{}\n}}".format(self.cache, self.callbacks, str(self.book))
