import datetime
import os
from functools import partial

from django.core.cache import cache, InvalidCacheBackendError
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest
from django.test.client import Client
from django.utils import translation
from django.utils.cache import get_cache_key as django_get_cache_key, get_cache, _generate_cache_key
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

import i18n
import settings
import topic_tools
from settings import LOG as logging
from updates.models import VideoFile
from utils.internet import generate_all_paths


# Signals

@receiver(post_save, sender=VideoFile)
def invalidate_on_video_update(sender, **kwargs):
    """
    Listen in to see when videos become available.
    """
    # Can only do full check in Django 1.5+, but shouldn't matter--we should only save with
    # percent_complete == 100 once.
    just_now_available = kwargs["instance"] and kwargs["instance"].percent_complete == 100 #and "percent_complete" in kwargs["updated_fields"]
    if just_now_available:
        # This event should only happen once, so don't bother checking if
        #   this is the field that changed.
        logging.debug("Invalidating cache on save for %s" % kwargs["instance"])
        invalidate_all_caches()

@receiver(pre_delete, sender=VideoFile)
def invalidate_on_video_delete(sender, **kwargs):
    """
    Listen in to see when available videos become unavailable.
    """
    was_available = kwargs["instance"] and kwargs["instance"].percent_complete == 100
    if was_available:
        logging.debug("Invalidating cache on delete for %s" % kwargs["instance"])
        invalidate_all_caches()

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


def backend_cache_page(handler, cache_time=settings.CACHE_TIME, cache_name=settings.CACHE_NAME):
    """
    Applies all logic for getting a page to cache in our backend,
    and never in the browser, so we can control things from Django/Python.

    This function does this all with the settings we want, specified in settings.
    """
    if caching_is_enabled():
        @condition(last_modified_func=partial(calc_last_modified, cache_name=cache_name))
        @cache_control(no_cache=True)  # must appear before @cache_page
        @cache_page(cache_time, cache=cache_name)
        def wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    else:
        # Would happen if caching was disabled
        def wrapper_fn(request, *args, **kwargs):
            return handler(request, *args, **kwargs)

    return wrapper_fn


# Importable functions

def caching_is_enabled():
    return settings.CACHE_TIME != 0

def get_web_cache():
    return get_cache(settings.CACHE_NAME) if caching_is_enabled() else None


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
        logging.warn("The cache item does not exist, and so could not be retrieved (path=%s)." % request.path)

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
        logging.warn("Did not create cache entry for %s" % path)


def expire_page(path=None, url_name=None, failure_ok=False):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    key = get_cache_key(path=path, url_name=url_name, failure_ok=failure_ok)

    if get_web_cache().has_key(key):
        get_web_cache().delete(key)


def invalidate_all_pages_related_to_video(video_id=None):
    """Given a video file, recurse backwards up the hierarchy and invalidate all pages.
    Also include video pages and related exercise pages.
    """

    # Expire all video files and related paths
    video_paths = topic_tools.get_video_page_paths(video_id=video_id)
    exercise_paths = topic_tools.get_exercise_page_paths(video_id=video_id)
    leaf_paths = set(video_paths).union(set(exercise_paths))

    for leaf_path in leaf_paths:
        all_paths = generate_all_paths(path=leaf_path, base_path=topic_tools.get_topic_tree()['path'])
        for path in filter(has_cache_key, all_paths):  # start at the root
            expire_page(path=path)


def regenerate_all_pages_related_to_videos(video_ids):
    """Same as above, but on a list of videos"""
    paths_to_regenerate = set() # unique set
    for video_id in video_ids:

        for video_path in topic_tools.get_video_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=video_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root
        for exercise_path in topic_tools.get_exercise_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=exercise_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root

    # Now, regenerate any page.
    for path in paths_to_regenerate:
        create_cache(path=path, force=True)

    return paths_to_regenerate


def invalidate_inmemory_caches():
    for module in (i18n, topic_tools):
        for cache_var in getattr(module, "CACHE_VARS", []):
            logging.debug("Emptying cache %s.%s" % (module.__name__, cache_var))
            setattr(module, cache_var, None)

    logging.info("Great success emptying the in-memory cache.")


def invalidate_web_cache():
    logging.debug("Clearing the web cache.")
    cache = get_web_cache()
    if cache:
        cache.clear()
    logging.debug("Great success emptying the web cache.")


def invalidate_all_caches():
    if settings.CACHE_TIME:
        invalidate_inmemory_caches()
        invalidate_web_cache()
