"""
"""
import os
import shutil
import tempfile
import random

from django.conf import settings
from django.core import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache

from kalite.testing.base import KALiteTestCase
from kalite.topic_tools import get_content_cache
from securesync.models import Device


class MainTestCase(KALiteTestCase):

    def __init__(self, *args, **kwargs):
        self.content_root = tempfile.mkdtemp() + "/"
        self.cache_dir = tempfile.mkdtemp() + "/"

        return super(MainTestCase, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        self.setUp_fake_contentroot()
        self.setUp_fake_cache()
        return super(KALiteTestCase, self).setUp(*args, **kwargs)

    def setUp_fake_contentroot(self):
        """
        Set up a location for the content folder that won't mess with the actual application.
        Because we're using call_command, the value of settings should persist
        into the videoscan command.
        """
        settings.CONTENT_ROOT = self.content_root

    def setUp_fake_cache(self):
        if settings.CACHE_TIME != 0:
            # Hackish way to create a temporary new file cache
            #settings.CACHES["file_based_cache"]["LOCATION"] = self.cache_dir
            #conf.settings.CACHES["file_based_cache"]["LOCATION"] = self.cache_dir
            #reload(cache)
            #reload(caching)
            self.web_cache = cache.get_cache(settings.CACHE_NAME)
            self.web_cache.clear()
            self.assertTrue(self.is_cache_empty(), "Check that cache is empty.")

    def tearDown(self):
        self.tearDown_fake_contentroot()
        self.tearDown_fake_cache()
        self.tearDown_fake_device()  # nothing to do

    def tearDown_fake_contentroot(self):
        shutil.rmtree(self.content_root)
        #for path in glob.glob(os.path.join(self.content_root, "*.mp4")):
        #    os.remove(path)

    def tearDown_fake_cache(self):
        shutil.rmtree(self.cache_dir)
        #for path in glob.glob(os.path.join(self.cache_dir, "*")):
        #    os.remove(path)

    def tearDown_fake_device(self):
        Device.own_device = None

    def is_cache_empty(self):
        return self.get_num_cache_entries() == 0

    def get_num_cache_entries(self):
        if isinstance(self.web_cache, FileBasedCache):
            return self.web_cache._num_entries

        elif isinstance(self.web_cache, LocMemCache):
            return len(self.web_cache._expire_info)
        else:
            assert False, "Only currently support FileBasedCache and LocMemCache"

    def create_random_content_file(self):
        """
        Helper function for testing content files.
        """
        content_id = random.choice(get_content_cache().keys())
        youtube_id = get_content_cache()[content_id]["youtube_id"]
        fake_content_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id)
        with open(fake_content_file, "w") as fh:
            fh.write("")
        self.assertTrue(os.path.exists(fake_content_file), "Make sure the content file was created, youtube_id='%s'." % youtube_id)
        return (fake_content_file, content_id, youtube_id)
