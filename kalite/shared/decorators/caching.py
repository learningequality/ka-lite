import datetime
import os
from functools import partial

from django.core.cache import InvalidCacheBackendError
from django.core.cache.backends.filebased import FileBasedCache
from django.utils.cache import get_cache_key, get_cache
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition 

import settings


def calc_last_modified(request, *args, **kwargs):
    """
    Returns the file's modified time as the last-modified date
    """
    assert "cache_name" in kwargs, "Must specify cache_name as a keyword arg."
    
    try:
        cache = get_cache(kwargs["cache_name"])
        assert isinstance(cache, FileBasedCache), "requires file-based cache."
    except InvalidCacheBackendError:
        return None

    key = get_cache_key(request, cache=cache)
    if key is None:
        return None

    fname = cache._key_to_file(cache.make_key(key))
    if not os.path.exists(fname):  # would happen only if cache expired AFTER getting the key
        return None
    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(fname))
    return last_modified


def backend_cache_page(handler, cache_time=settings.CACHE_TIME, cache_name="web_cache"):
    """
    Applies all logic for getting a page to cache in our backend,
    and never in the browser, so we can control things from Django/Python.

    This function does this all with the settings we want, specified in settings.
    """
    try:
        @condition(last_modified_func=partial(calc_last_modified, cache_name=cache_name))
        @cache_control(no_cache=True)  # must appear before @cache_page
        @cache_page(cache_time, cache=cache_name)
        def wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    except InvalidCacheBackendError:
        # Would happen if caching was disabled
        def wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    return wrapper_fn


