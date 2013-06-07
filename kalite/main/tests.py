"""
These will be run when you run "manage.py test [main].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test main --liveserver=localhost:8004-8010
".
"""

import logging
#import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from django.test import TestCase
from django.core.urlresolvers import reverse

import settings
from utils.testing import KALiteLocalTestCase, add_to_local_settings


class DeviceUnregisteredTest(KALiteLocalTestCase):
    """Validate all the steps of registering a device."""

    def test_device_registration(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browser.get(home_url) # Load page
        self.assertIn("Home", self.browser.title, "Homepage title")
        message = self.browser.find_element_by_id("container").find_element_by_xpath("//div[contains(@class,'message')]")
        self.assertIn("warning", message.get_attribute("class"), "warning message exists")
        self.assertIn("complete the setup", message.text, "warning message is for completing the setup.")
        
        # Make sure nobody is logged in
        login = self.browser.find_element_by_id("nav_login")
        self.assertIn("not-logged-in", login.get_attribute("class"), "Not (yet) logged in")
        
        # Now, log in as admin
        login.click()
        self.assertTrue(self.wait_for_page_change(home_url), "Clicked to change pages")
        self.assertIn("/login/", self.browser.current_url, "Login page url--we are on the login page")
        self.assertIn("Login", self.browser.title, "Login page title--we are on the login page")
        
        self.browser_activate_element(id="id_username")
        self.browser_send_keys(self.admin_user.username)
        self.browser_send_keys(Keys.TAB)
        self.browser_send_keys(self.admin_user.password)
        self.browser_send_keys(Keys.TAB)
        self.browser_send_keys(Keys.RETURN)
        
#        import pdb; pdb.set_trace()       
        

    
class DeviceAutoregisterTest(KALiteLocalTestCase):
    """"""
    
    def setUp(self):
        add_to_local_settings("INSTALL_CERTIFICATES", ["dummy_certificate"])
        super(DeviceAutoregisterTest,self).setUp()
    
    def tearDown(self):
        #import pdb; pdb.set_trace()
        #pass
        super(DeviceAutoregisterTest,self).tearDown()
        
    def test_device_registration(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")
