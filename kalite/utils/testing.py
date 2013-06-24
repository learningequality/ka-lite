"""
Contains test wrappers and helper functions for 
automated of KA Lite using selenium
for automated browser-based testing.
"""

import copy
import decorator
import logging
import time
import types
import os
import shutil
import sys
import platform
import tempfile
import unittest
from selenium import webdriver
from StringIO import StringIO

from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test import TestCase, LiveServerTestCase
from django_snippets._mkdir import _mkdir

import settings
from kalite.utils.django_utils import call_command_with_output


def x_only(f, cond, msg):
    """Decorator to label test classes or instance methods as x_only,
    x = "main" or "central"
    """

    # taken from unittest.skip
    if isinstance(f, (type, types.ClassType)):
        if not cond:
            f.__unittest_skip__ = True
            f.__unittest_skip_why__ = msg
        return f
        
    else:
        @unittest.skipIf(cond, msg)
        def wrapped_fn(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_fn


def distributed_only(f):
    """Run the test only on the distributed server"""
    return x_only(f, not settings.CENTRAL_SERVER, "Distributed server test")

def central_only(f):
    """Run the test only on the central server"""
    return x_only(f, settings.CENTRAL_SERVER, "Central server test")
    
        
def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""
    
    test_admin = User.objects.create_superuser(username, email, password)
    logging.debug('Created user "%s"' % username)

    # You'll need to log him in before you can send requests through the client
    client = Client()
    assert client.login(username=test_admin.username, password=password)

    # set dummy password, so it can be passed around
    test_admin.password = password
    assert client.login(username=test_admin.username, password=password)
    
    return test_admin
    
    
browser = None # persistent browser
def setup_test_env(browser_type="Firefox", test_user="test", test_password="test", test_email="test@learningequality.org", persistent_browser=False):
    """Create a django superuser, and connect to the specified browser.
    peristent_browser: keep a static handle to the browser, rather than 
      re-launch for every testcase.  True currently doesn't work well, so just do False :("""
      
    global browser
        
    # Add the test user
    admin_user = create_test_admin(username=test_user, password=test_password, email=test_email)
    
    # Launch the browser
    if not persistent_browser or (persistent_browser and not browser):
        local_browser = getattr(webdriver, browser_type)() # Get local session of firefox
        if persistent_browser: # share browser across tests
            browser = local_browser
    else:
        local_browser = browser
       
    return (local_browser,admin_user)
            


def wait_for_page_change(browser, source_url, wait_time=0.1, max_retries=50):
    """Given a selenium browser, wait until the browser has completed.
    Code taken from: https://github.com/dragoon/django-selenium/blob/master/django_selenium/testcases.py"""

    for i in range(max_retries):
        if browser.current_url == source_url:
            time.sleep(wait_time)
        else:
            break;

    return browser.current_url != source_url
    
    

class KALiteTestCase(LiveServerTestCase):
    """The base class for KA Lite test cases."""
    
    def __init__(self, *args, **kwargs):
        #create_test_admin()
        return super(KALiteTestCase, self).__init__(*args, **kwargs)
        
    def reverse(self, url_name):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name)

    
class BrowserTestCase(KALiteTestCase):
    """
    A base test case for Selenium, providing helper methods for generating
    clients and logging in profiles.
    """
    def __init__(self, *args, **kwargs):
        self.persistent_browser = False
        super(BrowserTestCase, self).__init__(*args, **kwargs)
        
    def setUp(self):
        """Create a browser to use for test cases.  Try a bunch of different browsers; hopefully one of them works!"""
        
        # Can use already launched browser.
        if self.persistent_browser:
            (self.browser,self.admin_user) = setup_test_env(persistent_browser=self.persistent_browser)
            
        # Must create a new browser to use
        else:
            for browser_type in ["Firefox", "Chrome", "Ie", "Opera"]:
                try:
                    (self.browser,self.admin_user) = setup_test_env(browser_type=browser_type)
                    break
                except Exception as e:
                    settings.LOG.debug("Could not create browser %s through selenium: %s" % (browser_type, e))
                    
        
    def tearDown(self):
        if not self.persistent_browser:
            self.browser.quit()
        
    def wait_for_page_change(self, source_url, wait_time=0.1, max_retries=50):
        """When testing, we have to make sure that the page has loaded before testing the resulting page."""
         
        return wait_for_page_change(self.browser, source_url, wait_time=wait_time, max_retries=max_retries)
    
    def browser_activate_element(self, elem=None, id=None, name=None, tag_name=None):
        """Given the identifier to a page element, make it active.
        Currently done by clicking TODO(bcipolli): this won't work for buttons, 
        so find another way when that becomes an issue."""
        
        if not elem:
            if id:
                elem = self.browser.find_element_by_id(id)
            elif name:
                elem = self.browser.find_element_by_name(name)
            elif tag_name:
                elem = self.browser.find_element_by_tag_name(tag_name)
        elem.click()
            
    def browser_send_keys(self, keys):
        """Convenience method to send keys to active_element in the browser"""
        self.browser.switch_to_active_element().send_keys(keys)

   
class KALiteCentralBrowserTestCase(BrowserTestCase):
    """Base class for central server test cases.
    They will have different functions in here, for sure.
    """
    pass
    
    
class KALiteLocalBrowserTestCase(BrowserTestCase):
    """Base class for main server test cases.
    They will have different functions in here, for sure.
    """
    pass


        
