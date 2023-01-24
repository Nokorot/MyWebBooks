
from ebooklib import epub

from .lib import Book, Chapter, Config
from .lib.callbacks import get_callback_class

import optparse, os, traceback, shutil, logging, sys

def parse_options():
    parser = optparse.OptionParser()
    parser.add_option('-c', '--clear-cache', dest='clear', default = False, action = 'store_true', help='Clears all local cache files, before loading the entry-pont webpage')
    parser.add_option('-i', '--ignore-cache', dest='ignore', default = False, action = 'store_true', help='Ignore all local cache files, when loading the files. Instead download an up-to-date version from the website and overwriting the cache if it exists.')
    parser.add_option('--config', dest='config', help='yaml config file')
    parser.add_option('-d', '--debug', dest='debug', default=False, action='store_true', help='enable debug output')
    parser.add_option('--toc-break', dest='toc_break', default=False, action='store_true', help='Only parse table of contents, useful when debugging a new web site')

    return parser.parse_args()


# sets up logger to go to stdout and enables debug logging when appropriate
def setup_logger(debug):
    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)

    if debug:
        root.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


def main():
    (options, args) = parse_options()

    setup_logger(options.debug)

    config = Config(options.config, options.debug, options.toc_break)
    config.ignore_cache = options.ignore;
    logging.getLogger().info(str(config))

    if options.clear and os.path.exists(config.cache):
        shutil.rmtree(config.cache)

    os.makedirs(config.cache, exist_ok=True)

    klass = get_callback_class(config.callbacks)

    book = Book(config, klass(config))
    book.load_html()

    try:
        fn = config.book.epub_filename
        epub_f = book.generate_epub()
        print(fn)

        epub.write_epub(fn, epub_f, {})
    except Exception as e:
        print(traceback.format_exc())
