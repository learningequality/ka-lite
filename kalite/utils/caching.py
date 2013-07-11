from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key as django_get_cache_key
from django.core.urlresolvers import reverse
from django.utils import translation
from django.test.client import Client

import settings
from utils.internet import generate_all_paths
from utils import topic_tools

def get_cache_key(path=None, url_name=None):
    """Call into Django to retrieve a cache key for the given url, or given url name
    
    NOTE: ONLY RETURNS CACHE_KEY IF THE CACHE_ITEM HAS BEEN CREATED ELSEWHERE!!!"""
    
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    request = HttpRequest()
    request.path = path if path else reverse(url_name)
    request.session = {'django_language': translation.get_language()}
    
    return django_get_cache_key(request)


def has_cache_key(path=None, url_name=None):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    return cache.has_key( get_cache_key(path=path, url_name=url_name) )


def create_cache(path=None, url_name=None, force=False):
    """Create a cache entry"""
    
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"

    if not path:
        path = reverse(url_name)

    if force:
        expire_page(path=path)
    if not has_cache_key(path=path):
        Client().get(path)


def expire_page(path=None,url_name=None):
    assert (path or url_name) and not (path and url_name), "Must have path or url_name parameter, but not both"
    
    key = get_cache_key(path=path, url_name=url_name)
    
    if cache.has_key(key):
        cache.delete(key)


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


def invalidate_cached_topic_hierarchies(video_id=None, video_slug=None):
    """Given a video file, recurse backwards up the hierarchy and invaliate all pages"""
    assert (video_id or video_slug) and not (video_id and video_slug), "One arg, not two" 

    # Expire all video files and related paths
    video_paths = get_video_page_paths(video_id=video_id, video_slug=video_slug)
    exercise_paths = get_exercise_page_paths(video_id=video_id, video_slug=video_slug)
    leaf_paths = set(video_paths).union(set(exercise_paths))

    for leaf_path in leaf_paths:
        for path in generate_all_paths(path=leaf_path, base_path=topic_tools.get_topic_tree()['path']): # start at the root
            expire_page(path=path)


def regenerate_cached_topic_hierarchies(video_ids):
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

