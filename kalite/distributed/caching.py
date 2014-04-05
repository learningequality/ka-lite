"""
Caching is a critical part of the KA Lite app, in order to speed up server response times.
However, if the server state changes, the cache may need to be invalidated.

This file exposes functions for clearing, or even pre-generating the cache.
It also implements listeners on some models to determine when the
cache needs to be invalidated.

For any app implementing cacheable data or writing to the web cache, the app should:
* Implement a CACHE_VARS variable, put cacheable variable values in there.  The values will be cleared,
    across all apps, by calling invalidate_inmemory_caches
* Call invalidate_web_cache (from fle_utils.internet.webcache)
"""
import datetime
import os
from functools import partial

from django.conf import settings; logging = settings.LOG
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

from fle_utils.internet import generate_all_paths
from fle_utils.internet.webcache import *
from kalite import i18n
from kalite.main import topic_tools
from kalite.updates.models import VideoFile


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


def create_cache_entry(path=None, url_name=None, cache=None, force=False):
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


def regenerate_all_pages_related_to_videos(video_ids):
    """Regenerate all webpages related to a specific list of videos.  This is good for increasing new server performance."""
    paths_to_regenerate = set() # unique set
    for video_id in video_ids:

        for video_path in topic_tools.get_video_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=video_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root
        for exercise_path in topic_tools.get_exercise_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=exercise_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root

    # Now, regenerate any page.
    for path in paths_to_regenerate:
        create_cache_entry(path=path, force=True)

    return paths_to_regenerate


def invalidate_inmemory_caches():
    """
    Any variables that are invalidated by things like content being added or deleted
    should be stored in the module's CACHE_VARS variable and registered here.

    This code clears all of those variables, so they are regenerated from scratch on
    the fly, using the new data.
    """
    # TODO: loop through all modules and see if a module variable exists, using getattr,
    #   rather than hard-coding.
    for module in (i18n, topic_tools):
        for cache_var in getattr(module, "CACHE_VARS", []):
            logging.debug("Emptying cache %s.%s" % (module.__name__, cache_var))
            setattr(module, cache_var, None)


def invalidate_all_caches():
    """
    Basic entry-point for clearing necessary caches.  Most functions can
    call in here.
    """
    if caching_is_enabled():
        invalidate_inmemory_caches()
        invalidate_web_cache()
        logging.debug("Great success emptying all caches.")
