"""
Test the topic-tree caching code (but only if caching is enabled in settings)
"""
import sys
import random
import requests
import urllib
import unittest

from django.test.client import Client

import settings
from kalite.main import topicdata
from utils import caching
from utils.django_utils import call_command_with_output
from utils.testing.base import KALiteTestCase
from utils.testing.decorators import distributed_only


@distributed_only
class CachingTest(KALiteTestCase):

    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_invalidation(self):
        """Create the cache item, then invalidate it and show that it is deleted."""
        
        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = random.choice(topicdata.NODE_CACHE['Video'].keys())
        sys.stdout.write("Testing on video_slug = %s\n" % video_slug)
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        
        # Create the cache item, and check it
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: no cache key after expiring the page")
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path), "expect: Cache key exists after Django Client get")

        # Invalidate the cache item, and check it
        caching.invalidate_cached_video_page(youtube_id) # test the convenience function
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: no cache key after expiring the page")

    
    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_across_clients(self):
        """Show that caching is accessible across all clients 
        (i.e. that different clients don't generate different cache keys)"""
        
        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = random.choice(topicdata.NODE_CACHE['Video'].keys())
        sys.stdout.write("Testing on video_slug = %s\n" % video_slug)
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: No cache key after expiring the page")
                
        # Set up the cache with Django client
        Client().get(video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "expect: Cache key exists after Django Client get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: No cache key after expiring the page")
                
        # Get the same cache key when getting with urllib, and make sure the cache is created again
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path), "expect: Cache key exists after urllib get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: No cache key after expiring the page")
        
        # Same deal, now using requests library
        requests.get(self.live_server_url + video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "expect: Cache key exists after requestsget")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: No cache key after expiring the page")
