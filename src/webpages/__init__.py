
def match_url(url):
    from ._webpages import _ALL_WM_CLASSES
    for wm_class in _ALL_WM_CLASSES:
        match = wm_class.match_url(url)
        if not match is None:
            return wm_class,  match

def get_wm_class(wm_class_name):
    # FIX: This is not relative
    mod = __import__('src.webpages._webpages', fromlist=[wm_class_name])
    try:
        return getattr(mod, wm_class_name)
    except AttributeError:
        return None
