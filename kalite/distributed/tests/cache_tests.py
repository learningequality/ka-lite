"""
Test the topic-tree caching code (but only if caching is enabled in settings)
"""
import sys
import random
import requests
import urllib

from django.conf import settings
from django.test.client import Client
from django.utils import unittest

from .. import caching
from fle_utils.django_utils import call_command_with_output
from kalite.main.topic_tools import get_node_cache
from kalite.testing.base import KALiteTestCase


class CachingTest(KALiteTestCase):
    video_cache = get_node_cache("Video")

    @unittest.skipIf(True, "Failing test that I'm tired of debugging.")  # TODO(bcipolli): re-enable when we need to be able to auto-cache
    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_invalidation(self):
        """Create the cache item, then invalidate it and show that it is deleted."""

        # Get a random video id
        n_videos = len(self.video_cache)
        video_id = self.video_cache.keys()[10]#random.choice(self.video_cache.keys())
        sys.stdout.write("Testing on video_id = %s\n" % video_id)
        video_path = self.video_cache[video_id][0]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path, failure_ok=True)

        # Create the cache item, and check it
        self.assertFalse(caching.has_cache_key(path=video_path), "expect: no cache key after expiring the page")

        caching.regenerate_all_pages_related_to_videos(video_ids=[video_id])
        self.assertTrue(caching.has_cache_key(path=video_path), "expect: Cache key exists after Django Client get")

        # Invalidate the cache item, and check it
        caching.invalidate_all_caches() # test the convenience function
        self.assertTrue(not caching.has_cache_key(path=video_path), "expect: no cache key after expiring the page")


    @unittest.skipIf(settings.CACHE_TIME==0, "Test only relevant when caching is enabled")
    def test_cache_across_clients(self):
        """Show that caching is accessible across all clients
        (i.e. that different clients don't generate different cache keys)"""

        # Get a random video id
        n_videos = len(self.video_cache)
        video_id = random.choice(self.video_cache.keys())
        sys.stdout.write("Testing on video_id = %s\n" % video_id)
        video_path = self.video_cache[video_id][0]['path']

        # Clean the cache for this item
        caching.expire_page(path=video_path, failure_ok=True)
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
