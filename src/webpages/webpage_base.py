
class WebpageManager_Base():
    download_config_enrtires = {
        "title": {'label': "Title"},
        "author": {'label': "author"},
        "language": {'label': "Language"},
        "cover_image": {'label': "Cover Image URL"},
        "include_images"  : {'label': 'Include Images', 'type': 'bool' },
     }

    def __init__(self, id, book):
        self.id = id
        self.book = book;

    # This function is meant to retrieve information like title, author and chapteres available from the books coverpage, that is the 'fiction page' in the case of royalroad
    def get_default_download_config_data(self):
        data = {}
        # book_data = webpage_manager.get_book_data(book)

        for key, value in self.download_config_enrtires.items():
            data[key] = value.copy() | \
                    { "name": key, 'value': getattr(self, 'get_default_book_%s' % key)() };
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
