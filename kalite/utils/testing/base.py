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
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

import settings
from shared import caching


def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""
    
    test_admin = User.objects.create_superuser(username, email, password)
    settings.LOG.debug('Created user "%s"' % username)

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
            settings.CACHES["web_cache"]["LOCATION"] = self.cache_dir
            conf.settings.CACHES["web_cache"]["LOCATION"] = self.cache_dir
            reload(cache)
            reload(caching)
            self.web_cache = cache.get_cache("web_cache")
            self.web_cache.clear()
            self.assertEqual(self.web_cache._num_entries, 0, "Check that cache is empty.")

    def tearDown(self):
        self.tearDown_fake_contentroot()
        self.tearDown_fake_cache()

    def tearDown_fake_contentroot(self):
        shutil.rmtree(self.content_root)
        #for path in glob.glob(os.path.join(self.content_root, "*.mp4")):
        #    os.remove(path)

    def tearDown_fake_cache(self):
        shutil.rmtree(self.cache_dir)
        #for path in glob.glob(os.path.join(self.cache_dir, "*")):
        #    os.remove(path)

    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name, args=args, kwargs=kwargs)

