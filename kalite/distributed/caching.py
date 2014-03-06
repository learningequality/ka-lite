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
from fle_utils.internet import generate_all_paths
from fle_utils.internet.webcache import *
from kalite.settings import LOG as logging
from main import topic_tools
from updates.models import VideoFile


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


def invalidate_all_caches():
    if settings.CACHE_TIME:
        invalidate_inmemory_caches()
        invalidate_web_cache()
        logging.debug("Great success emptying all caches.")
