"""
"""
import glob
import os
import random
import shutil
import tempfile

from django import conf
from django.conf import settings
from django.core import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache

from ..topic_tools import get_node_cache
from fle_utils.config.models import Settings
from kalite.testing.base import KALiteTestCase
from securesync.models import Device


class MainTestCase(KALiteTestCase):


    def __init__(self, *args, **kwargs):
        self.content_root = tempfile.mkdtemp() + "/"
        self.cache_dir = tempfile.mkdtemp() + "/"

        return super(MainTestCase, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        self.setUp_fake_contentroot()
        self.setUp_fake_cache()
        self.setUp_fake_device()
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

    def setUp_fake_device(self):
        """
        Fake the install process, to (quickly) make a key and set up the own_device()
        """
        # Could be a fixture, but safer to simply hard-code.
        Settings.set("public_key", u'MIIBCgKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8OrgL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9yTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8pyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZmlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvsLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQAB')
        Settings.set("private_key", u'-----BEGIN RSA PRIVATE KEY-----\nMIIEqQIBAAKCAQEAlbIPLnQH2dORFBK8i9x7/3E0DR571S01aP7M0TJD8vJf8Org\nL8pnru3o2Jaoni1XasCZgizvM4GNImk9geqPP/sFkj0cf/MXSLr1VDKo1SoflST9\nyTbOi7tzVuhTeL4P3LJL6PO6iNiWkjAdqp9QX3mE/DHh/Q40G68meRw6dPDI4z8p\nyUcshOpxAHTSh2YQ39LJAxP7YS26yjDX/+9UNhetFxemMrBZO0UKtJYggPYRlMZm\nlTZLBU4ODMmK6MT26fB4DC4ChA3BD4OFiGDHI/iSy+iYJlcWaldbZtc+YfZlGhvs\nLnJlrp4WYykJSH5qeBuI7nZLWjYWWvMrDepXowIDAQABAoIBAD8S/a6XGU/BA1ov\n4t4TkvO44TO96nOSTvTkl6x1v4e4dJBwhvHcGP/uIrRQFtA/TpwedxAQmuFa7vrW\n2SHKkX1l6Z0Kvt1yshblH8XQaq8WxqPzKDQGMdVSsHCoB7PScaCOR8nqGGjcyeTi\n/T0NT7JK46vX4N7dgttrE+WixOrtDOUJLX92tGSp8bZgg284fV053nJqYHHROpmZ\nCibM5HK8B/19ULCpglGQCUVmJPtRzNK1bE9OlB8P5aZzdEd82oC8TKfSGmByO1TI\nCat6x8e0hYVIDElYGdcW5CDAr6rbU0CXOxxQAz3gJFDe1/RbbGJEdjO3IulYbR4H\nBK+nGxECgYkA424wFuQGRAwig//SNasv5aIqz2qnczL5ob3MXCFR4aOMowS94qvd\neRG9McxgRwbEApOTMVMAUYlBMkKE//sBM9XWQ4q8igJ+TUlV8RRQ8AP6hMUhSXX0\nNeEECcauP4vI6hhsnTsG/OQ4pr/4bEewsyXFwPSGkh2v3O+fuc6A8RywQ3u6icc+\n9wJ5AKiACZmpSskyJgp+3X0jpYixb7pQ9gU6QpJmP9Z2DdUNnm0Y5tDjnaCd/Bvy\nmNuCWqNbYdlEYH32B3sCshzFCqQwkgSMOa84cHQHx4Nx7SG2fUp9w1ExvnMRzrnw\n3sjB3ptbNhk1yrkzhFbd6ZG4fsL5Mb0EurAFtQKBiFCUVc2GdQHfGsuR9DS3tnyx\n/GEI9NNIGFJKIQHzfENp4wZPQ8fwBMREmLfwJZyEtSYEi35KXi6FZugb0WuwzzhC\nZ2v+19Y+E+nmNeD4xcSEZFpuTeDtPd1pIDkmf85cBI+Mn88FfvBTHA9YrPgQXnba\nxzoaaSOUCR9Kd1kp5V2IQJtoVytBwPkCeFIDD6kkxuuqZu2Q1gkEgptHkZPjt/rP\nYnuTHNsrVowuNr/u8NkXEC+O9Zg8ub2NcsQzxCpVp4lnaDitFTf/h7Bmm4tvHNx1\n4fX3m1oU51ATXGQXVit8xK+JKU9DN4wLIGgJOwmGLwd5VZ5aIEb2v2vykgzn8l2e\nSQKBiQC7CJVToYSUWnDGwCRsF+fY9jUculveAQpVWj03nYBtBdTh2EWcvfoSjjfl\nmpzrraojpQlUhrbUf5MU1fD9+i6swrCCvfjXITG3c1bkkB5AaQW7NiPHvDRMuDpc\nHIQ+vqzdn4iUlt7KB5ChpnZMmgiOdCBM0vQsZlVCbp0ZNLqVYhFASQnWl6V9\n-----END RSA PRIVATE KEY-----\n')
        Device.initialize_own_device()

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

    def create_random_video_file(self):
        """
        Helper function for testing video files.
        """
        video_id = get_node_cache("Video").keys()[0]
        youtube_id = get_node_cache("Video")[video_id][0]["youtube_id"]
        fake_video_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id)
        with open(fake_video_file, "w") as fh:
            fh.write("")
        self.assertTrue(os.path.exists(fake_video_file), "Make sure the video file was created, youtube_id='%s'." % youtube_id)
        return (fake_video_file, video_id, youtube_id)

