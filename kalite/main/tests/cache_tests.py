"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import sys
import random
import requests
import urllib
import unittest

from django.test import TestCase, LiveServerTestCase
from django.core.management import call_command
from django.test.client import Client

import settings
from utils import caching
from kalite.main import topicdata
from utils.django_utils import call_command_with_output
from utils.testing import distributed_only


@distributed_only
class CachingTest(LiveServerTestCase):

    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_invalidation(self):

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
