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

class CachingTest(LiveServerTestCase):

    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_invalidation(self):

        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = random.sample(topicdata.NODE_CACHE['Video'].keys(), 1)[0]
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        
        # Create the cache item, and check it
        self.assertTrue(not caching.has_cache_key(path=video_path))
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path))

        # Invalidate the cache item, and check it
        #caching.expire_page(path=video_path)
        caching.invalidate_cached_video_page(youtube_id) # test the convenience function
        
        self.assertTrue(not caching.has_cache_key(path=video_path))

    
    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_across_clients(self):

        # Get a random youtube id
        n_videos = len(topicdata.NODE_CACHE['Video'])
        video_slug = random.sample(topicdata.NODE_CACHE['Video'].keys(), 1)[0]
        youtube_id = topicdata.NODE_CACHE['Video'][video_slug]['youtube_id']
        video_path = topicdata.NODE_CACHE['Video'][video_slug]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path)
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
                
        # Set up the cache with Django client
        Client().get(video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after Django Client get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
                
        # Get the same cache key when getting with urllib, and make sure the cache is created again
        urllib.urlopen(self.live_server_url + video_path).close()
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after urllib get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")
        
        # 
        requests.get(self.live_server_url + video_path)
        self.assertTrue(caching.has_cache_key(path=video_path), "Cache key exists after urllib get")
        caching.expire_page(path=video_path) # clean cache
        self.assertTrue(not caching.has_cache_key(path=video_path), "No cache key after expiring the page")


    @unittest.skipIf(settings.CACHE_TIME==0, "Test requires caching")
    def test_cache_maxentries(self):
        # Get a video and an exercise
        video_slug    = random.sample(topicdata.NODE_CACHE['Video'].keys(), 1)[0]
        exercise_slug = random.sample(topicdata.NODE_CACHE['Exercise'].keys(), 1)[0]

        settings.CACHES['default']['OPTIONS']['MAX_ENTRIES'] = 1

                
        # Make sure the cache is cleared
        out = call_command_with_output("cache", "clear")
        self.assertEquals(out[1], "", "No error output for 'cache clear'")
        self.assertEquals(out[2], 0, "Exit code = 0 for 'cache clear'")
        
        out = call_command_with_output("cache", "show")
        self.assertEquals(out[2], 0, "Exit code = 0 for 'cache show'")
        self.assertEquals(out[1], "", "No error output of 'cache show'")
        self.assertEquals(out[0].find("/"), -1, "No paths in output of 'cache show' after 'cache clear'")
        
        # Add one item to the cache and validate
        Client().get(topicdata.NODE_CACHE['Video'][video_slug]['path'])
        out = call_command_with_output("cache", "show")
        self.assertEquals(out[2], 0, "Exit code = 0 for 'cache show'")
        self.assertEquals(out[1], "", "No error output of 'cache show'")
        self.assertNotEquals(out[0].find(video_slug), -1, "Video slug in output of 'cache show' after 'get'")
        
        # Add another item to the cache and see that the previous was kicked out
        Client().get(topicdata.NODE_CACHE['Exercise'][exercise_slug]['path'])
        out = call_command_with_output("cache", "show")
        self.assertEquals(out[2], 0, "Exit code = 0 for 'cache show'")
        self.assertEquals(out[1], "", "No error output of 'cache show'")
        self.assertNotEquals(out[0].find(exercise_slug), -1, "Exercise slug in output of 'cache show' after 'get'")
        self.assertEquals(out[0].find(video_slug), -1, "Video slug in output of 'cache show' after 'get' of Exercise, with cache size=1")
        
        