
import requests
import os, io, hashlib
import json
from datetime import datetime

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

base_cache_dir="./cache"

#This information is send to the server with the request
# hdrs= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
# 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
# 'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
# 'Accept-Encoding': 'none',
# 'Accept-Language': 'en-US,en;q=0.8',
# 'Connection': 'keep-alive'}

hdrs = {"User-Agent": "Mozilla/5.0"}

def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def get_cache_filepath(url, fileext=None):
    if fileext is None:
        fileext = ''
    return os.path.join(base_cache_dir, get_url_hash(url)) + fileext

def is_valid_cache(cache_filepath):
    return os.path.isfile(cache_filepath)

def read_valid_cache_file(cache_filepath):
    with open(cache_filepath, 'rb') as f:
        return f.read()

def write_to_cache_file(content, cache_filepath):
    with open(cache_filepath, 'wb') as f:
        return f.write(content)

def get_data(url, fileext=None, cache_filepath=None, ignore_cache=False):
    if not ignore_cache:
        if cache_filepath is None:
            cache_filepath = get_cache_filepath(url, fileext)
        if is_valid_cache(cache_filepath):
            return read_valid_cache_file(cache_filepath)

    print(f"Downloading '{url}'")
    req = Request(url, headers=hdrs)
    with urlopen(req) as response:
        return response.read()

def get_and_cache_data(url, fileext=None, cache_filepath=None, ignore_cache=False):
    if ignore_cache:
        content = get_data(url, fileext, ignore_cache=True)
    else:
        if cache_filepath is None:
            cache_filepath = get_cache_filepath(url, fileext)
        if is_valid_cache(cache_filepath):
            return read_valid_cache_file(cache_filepath)
        content = get_data(url, fileext, ignore_cache=True)

    write_to_cache_file(content, cache_filepath)
    return content

def get_html(url, ignore_cache=False):
    content = get_data(url, fileext='.html', ignore_cache=ignore_cache)
    return BeautifulSoup(content, features="lxml")

def get_and_cache_html(url, ignore_cache=False):
    content = get_and_cache_data(url, fileext='.html', ignore_cache=ignore_cache)
    return BeautifulSoup(content, features="lxml")

def get_and_cache_image_data(url, ignore_cache=False, max_width=8096, max_height=8096):
    cache_filepath = "%s_%u_%u.jpg" % (get_cache_filepath(url, fileext=''), max_width, max_height)

    if not ignore_cache and is_valid_cache(cache_filepath):
        return read_valid_cache_file(cache_filepath)

    content = get_and_cache_data(url, fileext=None, ignore_cache=ignore_cache)

    content_io = io.BytesIO(content)

    from PIL import Image
    im = Image.open(content_io, 'r')
    # width, height = im.size

    im.thumbnail((max_width, max_height))

    # Check if the image has an alpha channel
    if im.mode in ("RGBA", "LA"):
        print("Image has an alpha channel. Converting to RGB...")
        im = im.convert("RGB")

    im.save(cache_filepath)
    return read_valid_cache_file(cache_filepath)

##The Following is not really tested but it is way to complicated anyway
#def get_and_cache_image_data(url, cache_info_filepath=None, ignore_cache=False, max_width=None, max_height=None):
#if cache_info_filepath is None:
#cache_info_filepath = get_cache_filepath(url, '.json')
#
#if ignoe_cache:
#cache_info = {}
#content = get_and_cache_data(url, fileext=None, ignoe_cache=True)
#elif os.path.isfile(cache_info_filepath):
## TODO: Life time
#cache_info = read_cache_info_file(cache_info_filepath)
#fileext = cache_info.get('fileext', '.jpg') # This is always .jpg
#
#cache_filepath = get_cache_filepath(url, fileext)
#
#width, height = cache_info['width'], cache_info['height']
#if (max_width is None or width <= max_width) \
#and (max_height is None or height <= max_height):
#return get_and_cache_data(url, cache_filepath, ignoe_cache=False)
#
#if max_width is None or ( height / max_height > width / max_width ):
#max_width = width * max_height // height
#
#scaled_cache_filepath = cache_info['scaled_widths'].get(max_width, None)
#if (not scaled_cache_filepath is None) and is_valid_cache(scaled_cache_filepath):
#return read_valid_cache_file(scaled_cache_filepath)
#
#content = get_data(url, fileext, cache_filepath, ignoe_cache=False)
#else:
#cache_info = {}
#content = get_data(url, fileext=None, ignoe_cache=True)
#
#content_io = io.BytesIO(content)
#
#from PIL import Image
#
#im = Image.open(content_io, 'r')
#width, height = im.size
#
#cache_info['width']   = width
#cache_info['height']  = height
#
#if max_width is None or ( height / max_height > width / max_width ):
#new_width = width * max_height // height
#new_height = max_height
#else:
#new_width = max_width
#new_height = height * max_width // width
#
#im = im.resize((new_width, new_height))
#scaled_cache_filepath = "%u_%s.%s" % (cache_filepath, new_width, fileext)
#im.save(scaled_cache_filepath)
#
#cache_info['scaled_widths'][new_width] = scaled_cache_filepath
#wrtie_cache_info_file(cache_info, cache_info_filepath)
#
#return read_valid_cache_file(scaled_cache_filepath)


##def load_and_cache_html(url, cache_filename, ignore_cache=False):
##with Network.load_and_cache(url, cache_filename, ignore_cache, 'r') as f:
##logging.getLogger().debug('Loading html dom from ' + cache_filename)
##
##return lxml.html.fromstring(f.read()) # .decode('utf-8', 'ignore')



"""
class CachedFile():
    _info = None

    def __init__(self, 
                 url, 
                 fileext=None, 
                 cache_filepath=None, 
                 ignore_cache=False,
                 cache_expire_time_delay=None):
        self.url = url
        if cache_filepath is None:
            self.cache_filepath = get_cache_filepath(url, fileext)
        else:
            self.cache_filepath = cache_filepath
        self.info_filepath = "%s_info.json" % cache_filepath

        self.cache_expire_time_delay = cache_expire_time_delay
        
    def get_data(self, ignore_cache=None):
        if ignore_cache is None:
            ignore_cache = False # self.ignore_cache

        if not ignore_cache:
            if self.is_valid():
                return self.load_valid_cache_file()

        # print(f"Downloading '{url}'");
        req = Request(self.url, headers=hdrs)
        with urlopen(req) as response:
            return response.read()

    def get_and_cache_data(self, ignore_cache=None, cache_expire_time_delay=None):
        content = self.get_data(ignore_cache);

        if cache_expire_time_delay is not None:
            expire_time = datetime.now() + cache_expire_time_delay; 
            self.set_expire_time(expire_time);
        
        if ignore_cache:
            content = self.get_data(ignroe_cache=True)
        else:
            if cache_filepath is None:
                cache_filepath = get_cache_filepath(surl, fileext)
            if is_valid_cache(cache_filepath):
                return read_valid_cache_file(cache_filepath)
            content = get_data(url, fileext, ignore_cache=True)

        write_to_cache_file(content, cache_filepath)
        return content


    # expire_time = datetime.now() + timedelta(days=1)

    def get_expire_time(self):
        if self._info is None:
            self.load_info_file()

        expire_time = self._info.get("expireTime", None)
        if expire_time is None:
            return None
        return datetime.fromtimestamp(expire_time)

    def set_expire_time(self, expire_time):
        if self._info is None:
            self.load_info_file()
        
        self._info()

    def is_valid(self):
        if not os.path.isfile(self.cache_filepath):
            return False
        
        expire_time = self.get_expire_time()
        if expire_time is not None and expire_time < datetime.now():
            return False

        return True

    def load_info_file(self):
        with open(self.info_filepath, 'r') as f:
            self._info = json.load(f)
    
    def save_info_file(self, info, cache_filepath):
        with open(self.info_filepath, 'w') as f:
            f.write(json.dumps(info))
"""





