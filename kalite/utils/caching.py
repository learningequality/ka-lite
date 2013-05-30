from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key
from django.core.urlresolvers import reverse

def expire_page(path=None,url_name=None):
    assert (path or url_name) and not (path and url_name)
    
    request = HttpRequest()
    request.path = path if path else reverse(url_name)
    
    key = get_cache_key(request)
    if cache.has_key(key):
        cache.delete(key)