from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key as django_get_cache_key, get_cache, _generate_cache_key
from django.core.urlresolvers import reverse
from django.utils import translation
from django.test.client import Client

import settings
from settings import LOG as logging
from utils.internet import generate_all_paths
from utils import topic_tools


def get_web_cache():
    return get_cache("web_cache") if settings.CACHE_TIME != 0 else None


def get_cache_key(path=None, url_name=None, cache=None, failure_ok=False):
    """Call into Django to retrieve a cache key for the given url, or given url name
    
    NOTE: ONLY RETURNS CACHE_KEY IF THE CACHE_ITEM HAS BEEN CREATED ELSEWHERE!!!"""
    
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    if not cache:
        cache = get_web_cache()

    request = HttpRequest()
    request.path = path or reverse(url_name)
    request.session = {'django_language': translation.get_language()}

    cache_key = django_get_cache_key(request, cache=get_web_cache())
    if not cache_key and not failure_ok:
        logging.warn("The cache item does not exist, and so could not be retrieved (path=%s)." % request.path)

    return cache_key


def has_cache_key(path=None, url_name=None, cache=None):
    if not cache:
        cache = get_web_cache()

    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    return get_web_cache().has_key( get_cache_key(path=path, url_name=url_name, failure_ok=True, cache=cache) )


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


def expire_page(path=None,url_name=None):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"
    
    key = get_cache_key(path=path, url_name=url_name)
    
    if get_web_cache().has_key(key):
        get_web_cache().delete(key)


def get_video_page_paths(video_id=None, video_slug=None):
    assert (video_id or video_slug) and not (video_id and video_slug), "One arg, not two" 

    try:
        if not video_slug:
            video_slug = topic_tools.get_id2slug_map()[video_id]
        
        return topic_tools.get_node_cache("Video")[video_slug]['paths']
    except:
        return []


def get_exercise_page_paths(video_id=None, video_slug=None):
    assert (video_id or video_slug) and not (video_id and video_slug), "One arg, not two" 

    try:
        exercise_paths = set()
        for exercise in get_related_exercises(video=topic_tools.get_node_cache("Video")[video_slug]):
            exercise_paths = exercise_paths.union(set(exercise["paths"]))
        return list(exercise_paths)
    except:
        return []


def invalidate_all_pages_related_to_video(video_id=None, video_slug=None):
    """Given a video file, recurse backwards up the hierarchy and invalidate all pages.
    Also include video pages and related exercise pages.
    """
    assert (video_id or video_slug) and not (video_id and video_slug), "One arg, not two" 

    # Expire all video files and related paths
    video_paths = get_video_page_paths(video_id=video_id, video_slug=video_slug)
    exercise_paths = get_exercise_page_paths(video_id=video_id, video_slug=video_slug)
    leaf_paths = set(video_paths).union(set(exercise_paths))

    for leaf_path in leaf_paths:
        all_paths = generate_all_paths(path=leaf_path, base_path=topic_tools.get_topic_tree()['path'])
        for path in filter(has_cache_key, all_paths):  # start at the root
            expire_page(path=path)


def regenerate_all_pages_related_to_videos(video_ids):
    """Same as above, but on a list of videos"""
    paths_to_regenerate = set() # unique set
    for video_id in video_ids:

        for video_path in get_video_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=video_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root
        for exercise_path in get_exercise_page_paths(video_id=video_id):
            paths_to_regenerate = paths_to_regenerate.union(generate_all_paths(path=exercise_path, base_path=topic_tools.get_topic_tree()['path']))  # start at the root

    # Now, regenerate any page.
    for path in paths_to_regenerate:
        create_cache(path=path, force=True)

    return paths_to_regenerate
