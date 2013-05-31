from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key as django_get_cache_key
from django.core.urlresolvers import reverse

# all code based on Django snippet at:
#   http://djangosnippets.org/snippets/936/

def get_cache_key(path=None, url_name=None):
    """Call into Django to retrieve a cache key for the given url, or given url name
    
    NOTE: ONLY RETURNS CACHE_KEY IF THE CACHE_ITEM HAS BEEN CREATED ELSEWHERE!!!"""
    
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    request = HttpRequest()
    request.path = path if path else reverse(url_name)
    
    return django_get_cache_key(request)


def has_cache_key(path=None, url_name=None):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    return cache.has_key( get_cache_key(path=path, url_name=url_name) )


def expire_page(path=None,url_name=None):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"
    
    key = get_cache_key(path=path, url_name=url_name)
    
    if cache.has_key(key):
        cache.delete(key)