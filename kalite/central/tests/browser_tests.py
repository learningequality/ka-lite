"""
These will be run when you run "manage.py test [central].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test central --liveserver=localhost:8004-8010
".
"""

import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from django.test import TestCase
from django.core.urlresolvers import reverse

import settings
from utils.testing import central_only, KALiteCentralBrowserTestCase


#@central_only
class SuperUserTest(KALiteCentralBrowserTestCase):
    """Log in the super user"""

    def test_superuser_login(self):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("auth_login")
        
        self.browser.get(login_url) # Load page
        self.assertIn("Log in", self.browser.title, "Login page title")
        
        # Focus should be on username, pasword and submit
        #   should be accessible through keyboard only.
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser.switch_to_active_element().send_keys(self.admin_user.username + Keys.TAB)
        self.browser.switch_to_active_element().send_keys("test" + Keys.TAB)
        self.browser.switch_to_active_element().send_keys(Keys.RETURN)
        
        # Make sure that the page changed to the admin homepage
        self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
        self.assertIn(reverse("homepage"), self.browser.current_url, "Login browses to homepage (account admin)" )
        self.assertIn("Account administration", self.browser.title, "Check account admin page title")
        
        
#@central_only
class OrgUserRegistrationTest(KALiteCentralBrowserTestCase):
    user_email = "test_user@nowhere.com"
    password   = "password"
    org_name = "test org"

    def test_user_register(self):
        """Tests that a user can register"""
         
        register_url = self.reverse("registration_register")

        self.browser.get(register_url) # Load page
        self.assertIn("Sign up", self.browser.title, "Login page title")
        
        # Part 1: REGISTER
        self.browser_activate_element(id="id_first_name") # explicitly set the focus, to start
        self.browser_send_keys("Firstname" + Keys.TAB) # first name
        self.browser_send_keys("Lastname" + Keys.TAB) # last name
        self.browser_send_keys(self.user_email + Keys.TAB) #email
        self.browser_send_keys(self.org_name + Keys.TAB) #org name
        self.browser_send_keys(Keys.TAB) # organization dropdown (skipped)
        self.browser_send_keys(self.password + Keys.TAB) #password
        self.browser_send_keys(self.password + Keys.TAB) #password (again)
        self.browser_send_keys(Keys.TAB) # subscribe checkbox (skipped)
        self.browser_send_keys(Keys.SPACE + Keys.TAB) # checkbox 1
        self.browser_send_keys(Keys.TAB) # Usage Ts and Cs link (skipped)
        self.browser_send_keys(Keys.SPACE + Keys.TAB) # checkbox 2
        self.browser_send_keys(Keys.TAB) # API Ts and Cs link (skipped)

        # This runs, but captures nothing.  
        # TODO(bcipolli): figure out why this is empty,
        #   capture the activation email.  Then, activate
        #   the account.
        # Also need to set settings dynamically to output
        #   email to stdout
        #str = self.capture_stdout((self.browser_send_keys, Keys.RETURN))
        self.browser_send_keys(Keys.RETURN)

                
        # Make sure that the page changed to the admin homepage
        self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
        self.assertIn(reverse("registration_complete"), self.browser.current_url, "Register browses to thank you page" )
        self.assertIn("Registration complete", self.browser.title, "Check registration complete title")
