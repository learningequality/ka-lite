from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key as django_get_cache_key
from django.core.urlresolvers import reverse
from django.utils import translation
from django.test.client import Client

import settings
from main import topicdata
from utils import topic_tools, internet

# all code based on Django snippet at:
#   http://djangosnippets.org/snippets/936/


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
        

def get_video_page_path(video_id=None, video_slug=None):
    # only import for this specific function

    assert (video_id or video_slug) and not (video_id and video_slug), "One arg, not two" 
        
    from kalite.main import topicdata

    try:
        if not video_slug:
            video_slug = topicdata.ID2SLUG_MAP[video_id]
        
        return topicdata.NODE_CACHE["Video"][video_slug]['path']
    except:
        return None
    
    
def invalidate_cached_video_page(video_id=None, video_slug=None, video_path=None):
    """Convenience function for expiring a video page"""

    assert (video_id or video_path or video_slug) and not (video_id and video_slug and video_path), "One arg, not two" 

    if not video_path:
        video_path = get_video_page_path(video_id=video_id, video_slug=video_slug)
                    
    # Clean the cache for this item
    expire_page(path=video_path)


def invalidate_cached_topic_hierarchy(video_id=None, video_slug=None, video_path=None):
    """Given a video file, recurse backwards up the hierarchy and invaliate all pages"""
    assert (video_id or video_path or video_slug) and not (video_id and video_slug and video_path), "One arg, not two" 

    if not video_path:
        video_path = get_video_page_path(video_id=video_id, video_slug=video_slug)

    for path in internet.generate_all_paths(path=video_path, base_path=topicdata.TOPICS['path']): # start at the root
        expire_page(path=path)


def regenerate_cached_topic_hierarchies(video_ids):
    """Same as above, but on a list of videos"""
    paths_to_regenerate = set() # unique set
    for video_id in video_ids:
        video_path = get_video_page_path(video_id=video_id)

        paths_to_regenerate = paths_to_regenerate.union(internet.generate_all_paths(path=video_path, base_path=topicdata.TOPICS['path'])) # start at the root

    # Now, regenerate any page.
    for path in paths_to_regenerate:
        create_cache(path=path, force=True)

