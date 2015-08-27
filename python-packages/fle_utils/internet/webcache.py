"""
"""
import datetime
import os
from functools import partial

from django.conf import settings
from django.core.cache import cache, InvalidCacheBackendError
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test.client import Client
from django.utils import translation
from django.utils.cache import get_cache_key as django_get_cache_key, get_cache
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition


# Decorators

def calc_last_modified(request, *args, **kwargs):
    """
    Returns the file's modified time as the last-modified date
    """
    assert "cache_name" in kwargs, "Must specify cache_name as a keyword arg."

    try:
        cache = get_cache(kwargs["cache_name"])
        assert isinstance(cache, FileBasedCache) or isinstance(cache, LocMemCache), "requires file-based or mem-based cache."
    except InvalidCacheBackendError:
        return None

    key = django_get_cache_key(request, cache=cache)
    if key is None or not cache.has_key(key):
        return None

    if isinstance(cache, FileBasedCache):
        fname = cache._key_to_file(cache.make_key(key))
        if not os.path.exists(fname):  # would happen only if cache expired AFTER getting the key
            return None
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(fname))

    elif isinstance(cache, LocMemCache):
        # It's either in the cache (and valid), and therefore anything since the server
        #   started would be fine.
        # Or, it's not in the cache at all.
        creation_time = cache._expire_info[cache.make_key(key)] - settings.CACHE_TIME
        last_modified = datetime.datetime.fromtimestamp(creation_time)

    return last_modified


def backend_cache_page(handler, cache_time=None, cache_name=None):
    """
    Applies all logic for getting a page to cache in our backend,
    and never in the browser, so we can control things from Django/Python.

    This function does this all with the settings we want, specified in settings.
    """

    if not cache_time:
        cache_time = settings.CACHE_TIME

    if not cache_name:
        cache_name = "default"

    if caching_is_enabled():
        @condition(last_modified_func=partial(calc_last_modified, cache_name=cache_name))
        @cache_control(no_cache=True)  # must appear before @cache_page
        @cache_page(cache_time, cache=cache_name)
        def backend_cache_page_wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    else:
        # Would happen if caching was disabled
        def backend_cache_page_wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    return backend_cache_page_wrapper_fn


# Importable functions

def caching_is_enabled():
    return settings.CACHE_TIME != 0

def get_web_cache():
    return get_cache('default') if caching_is_enabled() else None


def get_cache_key(path=None, url_name=None, cache=None, failure_ok=False):
    """Call into Django to retrieve a cache key for the given url, or given url name

    NOTE: ONLY RETURNS CACHE_KEY IF THE CACHE_ITEM HAS BEEN CREATED ELSEWHERE!!!"""

    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    if not cache:
        cache = get_web_cache()

    request = HttpRequest()
    request.path = path or reverse(url_name)
    request.session = {settings.LANGUAGE_COOKIE_NAME: translation.get_language()}

    cache_key = django_get_cache_key(request, cache=get_web_cache())
    if not cache_key and not failure_ok:
        pass#logging.warn("The cache item does not exist, and so could not be retrieved (path=%s)." % request.path)

    return cache_key


def has_cache_key(path=None, url_name=None, cache=None):
    if not cache:
        cache = get_web_cache()

    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    if not cache:
        return False
    else:
        return cache.has_key( get_cache_key(path=path, url_name=url_name, failure_ok=True, cache=cache) )


def create_cache(path=None, url_name=None, cache=None, force=False):
    """Create a cache entry"""

    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"
    if not cache:
        cache = get_web_cache()

    if not path:
        path = reverse(url_name)
    if force and has_cache_key(path=path, cache=cache):
        expire_page(path=path)
        assert not has_cache_key(path=path, cache=cache)
    if not has_cache_key(path=path, cache=cache):
        Client().get(path)

    if not has_cache_key(path=path, cache=cache):
        pass#logging.warn("Did not create cache entry for %s" % path)


def expire_page(path=None, url_name=None, failure_ok=False):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    key = get_cache_key(path=path, url_name=url_name, failure_ok=failure_ok)

    if get_web_cache().has_key(key):
        get_web_cache().delete(key)


def invalidate_web_cache():
    cache = get_web_cache()
    if cache:
        cache.clear()
