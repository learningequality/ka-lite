"""
Contains test wrappers and helper functions for 
automated of KA Lite using selenium
for automated browser-based testing.
"""
import glob
import os
import shutil
import tempfile

from django import conf
from django.contrib.auth.models import User
from django.core import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import LiveServerTestCase

import settings
from config.models import Settings
from securesync.models import Device
from shared import caching


def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""
    
    test_admin = User.objects.create_superuser(username, email, password)

    # You'll need to log him in before you can send requests through the client
    client = Client()
    assert client.login(username=test_admin.username, password=password)

    # set dummy password, so it can be passed around
    test_admin.password = password
    assert client.login(username=test_admin.username, password=password)
    
    return test_admin
    
    

class KALiteTestCase(LiveServerTestCase):
    """The base class for KA Lite test cases."""
    
    def __init__(self, *args, **kwargs):
        self.content_root = tempfile.mkdtemp() + "/"
        self.cache_dir = tempfile.mkdtemp() + "/"

        return super(KALiteTestCase, self).__init__(*args, **kwargs)


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
        #self.tearDown_fake_device()  # nothing to do

    def tearDown_fake_contentroot(self):
        shutil.rmtree(self.content_root)
        #for path in glob.glob(os.path.join(self.content_root, "*.mp4")):
        #    os.remove(path)

    def tearDown_fake_cache(self):
        shutil.rmtree(self.cache_dir)
        #for path in glob.glob(os.path.join(self.cache_dir, "*")):
        #    os.remove(path)

    def is_cache_empty(self):
        return self.get_num_cache_entries() == 0

    def get_num_cache_entries(self):
        if isinstance(self.web_cache, FileBasedCache):
            return self.web_cache._num_entries

        elif isinstance(self.web_cache, LocMemCache):
            return len(self.web_cache._expire_info)
        else:
            assert False, "Only currently support FileBasedCache and LocMemCache"

    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name, args=args, kwargs=kwargs)

