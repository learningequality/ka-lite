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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from StringIO import StringIO

from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test import TestCase, LiveServerTestCase
from django.utils import unittest

import settings
from registration.models import RegistrationProfile
from securesync.models import FacilityUser
from utils.django_utils import call_command_with_output


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

    if User.objects.filter(username__iexact=username).count() != 0:
        return

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
def setup_test_env(browser_type="Firefox", test_user="testadmin", test_password="test", test_email="test@learningequality.org", persistent_browser=False):
    """Create a django superuser, and connect to the specified browser.
    peristent_browser: keep a static handle to the browser, rather than 
      re-launch for every testcase.  True currently doesn't work well, so just do False :("""
      
    global browser

    # Launch the browser
    if not persistent_browser or (persistent_browser and not browser):
        local_browser = getattr(webdriver, browser_type)() # Get local session of firefox
        if persistent_browser: # share browser across tests
            browser = local_browser
    else:
        local_browser = browser

    # Add the test user (only after the browser succeeds)
    admin_user = create_test_admin(username=test_user, password=test_password, email=test_email)

    return (local_browser,admin_user,test_password)


def browse_to(browser, dest_url, wait_time=0.1, max_retries=50):
    """Given a selenium browser, open the given url and wait until the browser has completed."""
    if dest_url == browser.current_url:
        return True
         
    source_url = browser.current_url
    page_source = browser.page_source
    
    browser.get(dest_url)
    
    return wait_for_page_change(browser, source_url=source_url, page_source=page_source, wait_time=wait_time, max_retries=max_retries)
    

def wait_for_page_change(browser, source_url=None, page_source=None, wait_time=0.1, max_retries=50):
    """Given a selenium browser, wait until the browser has completed.
    Code taken from: https://github.com/dragoon/django-selenium/blob/master/django_selenium/testcases.py"""

    for i in range(max_retries):
        if source_url is not None and browser.current_url != source_url:
            break
        elif page_source is not None and browser.page_source != page_source:
            break
        else:
            time.sleep(wait_time)

    return browser.current_url != source_url
    
    

class KALiteTestCase(LiveServerTestCase):
    """The base class for KA Lite test cases."""

    def __init__(self, *args, **kwargs):
        return super(KALiteTestCase, self).__init__(*args, **kwargs)

    def reverse(self, url_name, *args, **kwargs):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name, *args, **kwargs)

    
class BrowserTestCase(KALiteTestCase):
    """
    A base test case for Selenium, providing helper methods for generating
    clients and logging in profiles.
    """
    def __init__(self, *args, **kwargs):
        self.persistent_browser = False
        self.max_wait_time = kwargs.get("max_wait_time", 30)
        return super(BrowserTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Create a browser to use for test cases.  Try a bunch of different browsers; hopefully one of them works!"""

        super(BrowserTestCase, self).setUp()

        # Can use already launched browser.
        if self.persistent_browser:
            (self.browser,self.admin_user,self.admin_pass) = setup_test_env(persistent_browser=self.persistent_browser)

        # Must create a new browser to use
        else:
            for browser_type in ["Firefox", "Chrome", "Ie", "Opera"]:
                try:
                    (self.browser,self.admin_user,self.admin_pass) = setup_test_env(browser_type=browser_type)
                    break
                except Exception as e:
                    settings.LOG.debug("Could not create browser %s through selenium: %s" % (browser_type, e))


    def tearDown(self):
        if not self.persistent_browser:
            self.browser.quit()
        return super(BrowserTestCase, self).tearDown()

    def browse_to(self, dest_url, wait_time=0.1, max_retries=50):
        """When testing, we have to make sure that the page has loaded before testing the resulting page."""

        self.assertTrue(browse_to(self.browser, dest_url=dest_url, wait_time=wait_time, max_retries=max_retries), "Browsing to '%s'" % dest_url)

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


    def check_django_message(self, message_type=None, contains=None, exact=None, num_messages=1):
        """Both central and distributed servers use the Django messaging system.
        This code will verify that a message with the given type contains the specified text."""

        time.sleep(0.50) # wait for the message to get created via AJAX

        # Get messages (and limit by type)    
        messages = self.browser.find_elements_by_class_name("message")
        if type:
            messages = [m for m in messages if message_type in m.get_attribute("class")]

        # Check that we got as many as expected
        if num_messages is not None:
            self.assertEqual(num_messages, len(messages)), "Make sure there are %d message(s), type='%s'." % (num_messages, message_type if message_type else "(any)")

        for message in messages:
            if contains is not None:
                self.assertIn(contains, message.text, "Make sure message contains '%s'" % contains)
            if exact is not None:
                self.assertEqual(exact, message.text, "Make sure message = '%s'" % exact)


class KALiteCentralBrowserTestCase(BrowserTestCase):
    """Base class for central server test cases.
    They will have different functions in here, for sure.
    """

    def register_user(self, username, password, first_name="firstname", last_name="lastname", org_name="test org", expect_success=True):
        """Tests that a user can register"""
         
        register_url = self.reverse("registration_register")

        self.browse_to(register_url) # Load page
        self.assertIn("Sign up", self.browser.title, "Register page title")
        
        # Part 1: REGISTER
        self.browser_activate_element(id="id_first_name") # explicitly set the focus, to start
        self.browser_send_keys(first_name + Keys.TAB) # first name
        self.browser_send_keys(last_name + Keys.TAB) # last name
        self.browser_send_keys(username + Keys.TAB) #email
        self.browser_send_keys(org_name + Keys.TAB) #org name
        self.browser_send_keys(Keys.TAB) #skip org expansion
        self.browser_send_keys(password + Keys.TAB) #password
        self.browser_send_keys(password + Keys.TAB) #password (again)
        self.browser_send_keys(Keys.TAB) # skip newsletter subscribe
        self.browser_send_keys(Keys.SPACE + Keys.TAB + Keys.TAB) # agree to terms 1, skip link
        self.browser_send_keys(Keys.SPACE + Keys.TAB + Keys.TAB) # agree to terms 2, skip link

        # We could capture the activation link, but we'll just cheat
        #   by querying the value directly in the "activate user" function.
        self.browser_send_keys(Keys.RETURN)
        
        
        # Make sure that the page changed to the "thank you" confirmation page
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(reverse("registration_complete"), self.browser.current_url, "Register browses to thank you page" )
            self.assertIn("Registration complete", self.browser.title, "Check registration complete title")



    def activate_user(self, username, expect_success=True):
        """After user was registered, do account activation"""
        
        # Get the activation url, then browse there.
        user = User.objects.get(username=username)
        profile = RegistrationProfile.objects.get(user=user)
        activation_key = profile.activation_key
        self.assertNotEqual(activation_key, "ALREADY_ACTIVATED", "Make sure the user wasn't already activated.")
        
        activation_url = self.reverse('registration_activate', kwargs={ 'activation_key': activation_key });
        self.browse_to(activation_url)
        
        # Verify what we see!
        if expect_success:
            self.check_django_message(message_type="success", contains="Your account is now activ", num_messages=1)


    def login_user(self, username, password, expect_success=True):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("auth_login")
        self.browse_to(login_url) # Load page
        self.assertIn("Log in", self.browser.title, "Login page title")
        
        # Focus should be on username, pasword and submit
        #   should be accessible through keyboard only.
        self.browser.find_element_by_id("id_username").clear()
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser.switch_to_active_element().send_keys(username + Keys.TAB)
        self.browser.switch_to_active_element().send_keys(password + Keys.TAB)
        self.browser.switch_to_active_element().send_keys(Keys.RETURN)
        
        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            self.assertIn(reverse("homepage"), self.browser.current_url, "Login browses to homepage (account admin)" )
            self.assertIn("Account administration", self.browser.title, "Check account admin page title")

        
    def logout_user(self):
        if self.is_logged_in():
            if self.reverse("homepage") in self.browser.current_url:
                self.browser.get(self.reverse("auth_logout"))
            else:
                self.browse_to(self.reverse("auth_logout"))
                
            self.assertIn(reverse("homepage"), self.browser.current_url, "Logout browses to homepage" )
            self.assertFalse(self.is_logged_in(), "Make sure that user is no longer logged in.")

    def is_logged_in(self, username=None):
        elements = self.browser.find_elements_by_id("logout")
        
        if len(elements)==0:
            return False
        elif username is None:
            return True
        else:
            return elements[0].text.startswith(username + " ")


class KALiteDistributedBrowserTestCase(BrowserTestCase):
    """Base class for main server test cases.
    They will have different functions in here, for sure.
    """

    def register_user(self, username, password, first_name="firstname", last_name="lastname", stay_logged_in=False, expect_success=True):
        """Tests that a user can register"""

        # Expected results vary based on whether a user is logged in or not.
        if not stay_logged_in:
            self.logout_user()

        register_url = self.reverse("add_facility_student")
        self.browse_to(register_url) # Load page
        self.assertIn("Sign up", self.browser.title, "Register page title")

        # Part 1: REGISTER
        self.browser_activate_element(id="id_username") # explicitly set the focus, to start
        self.browser_send_keys(username + Keys.TAB) # username
        self.browser_send_keys(first_name + Keys.TAB) # first name
        self.browser_send_keys(last_name + Keys.TAB) # last name
        self.browser_send_keys(password + Keys.TAB) #password
        self.browser_send_keys(password + Keys.TAB) #password check

        self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(reverse("login"), self.browser.current_url, "Register browses to login page" )
            #self.check_django_message(message_type="success", contains="You successfully registered.")
            # uncomment message check when that code gets checked in

    def login_user(self, username, password, expect_success=True):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("login")
        self.browse_to(login_url) # Load page
        self.assertIn("Log in", self.browser.title, "Login page title")

        # Focus should be on username, pasword and submit
        #   should be accessible through keyboard only.
        self.browser.find_element_by_id("id_username").clear() # explicitly set the focus, to start
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser.switch_to_active_element().send_keys(username + Keys.TAB)
        self.browser.switch_to_active_element().send_keys(password + Keys.TAB)
        self.browser.switch_to_active_element().send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            time.sleep(0.5)  # allow async status to update
            
            user_obj = FacilityUser.objects.filter(username__iexact=username)
            # Username is case-insensitive now, but wasn't in the past.
            #   So we need to dance a little bit in case there are two users with the
            #   same username (different cases)--in that case, case matters!
            #
            # Note that if a facilityuser isn't logging in (i.e. an admin), the above returns count==0
            logged_in_username = username if user_obj.count() != 1 else user_obj[0].username
            self.assertTrue(self.is_logged_in(logged_in_username), "make sure %s is logged in." % username)


    def login_admin(self, username=None, password=None, expect_success=True):
        if username is None:
            username = self.admin_user.username
        if password is None:
            password = self.admin_pass

        self.login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("easy_admin"), self.browser.current_url, "Login browses to easy_admin page" )


    def login_teacher(self, username, password, expect_success=True):
        self.login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("coach_reports"), self.browser.current_url, "Login browses to coach reports page" )
            self.check_django_message("success", contains="You've been logged in!")


    def login_student(self, username, password, expect_success=True):
        self.login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("homepage"), self.browser.current_url, "Login browses to homepage" )
            self.check_django_message("success", contains="You've been logged in!")


    def logout_user(self):
        if self.is_logged_in():
            # Since logout redirects to the homepage, browse_to will fail (with no good way to avoid).
            #   so be smarter in that case.
            if self.reverse("homepage") in self.browser.current_url:
                self.browser.get(self.reverse("logout"))
            else:
                self.browse_to(self.reverse("logout"))
            self.assertIn(reverse("homepage"), self.browser.current_url, "Logout browses to homepage" )
            self.assertFalse(self.is_logged_in(), "Make sure that user is no longer logged in.")


    def is_logged_in(self, expected_username=None):
        # Two ways to be logged in:
        # 1. Student: #logged-in-name is username
        # 2. Admin: #logout contains username
        logged_in_name_text = self.browser.find_element_by_id("logged-in-name").text
        logout_text = self.browser.find_element_by_id("logout").text
        username_text =  logged_in_name_text or logout_text[0:-len(" (LOGOUT)")]
        
        # Just checking to see if ANYBODY is logged in
        if not expected_username:
            return username_text != "" 
        # Checking to see if Django user, or user with missing names is logged in
        #   (then username displays)
        elif username_text.lower() == expected_username.lower():
            return True
        # Checking to see if a FacilityUser with a filled-in-name is logged in
        else:
            user_obj = FacilityUser.objects.filter(username=expected_username)
            if user_obj.count() == 0:  # couldn't find the user, they can't be logged in
                if FacilityUser.objects.filter(username__iexact=expected_username).count() != 0:
                    assert username_text == "", "We don't have a valid user object, but someone's logged in; looks like you sent in the wrong username case."
                else:
                    assert username_text == "", "Impossible for anybody to be logged in; no recognizable user of that username exists!"
            else:
                return username_text.lower() == user_obj[0].get_name().lower()


class KALiteRegisteredDistributedBrowserTestCase(KALiteDistributedBrowserTestCase):
    """Same thing, but do the setup steps to register a facility."""
    facility_name = "Test Facility"
    
    def setUp(self):
        """Add a facility, so users can begin registering / logging in immediately."""

        super(KALiteRegisteredDistributedBrowserTestCase,self).setUp() # sets up admin, etc

        self.add_facility(facility_name=self.facility_name)
        self.logout_user()

    def add_facility(self, facility_name):
        """Add a facility"""

        # Login as admin
        self.login_admin()

        # Add the facility
        add_facility_url = self.reverse("add_facility", kwargs={"id": "new"})
        self.browse_to(add_facility_url)

        self.browser_activate_element(id="id_name") # explicitly set the focus, to start
        self.browser_send_keys(facility_name)
        self.browser.find_elements_by_class_name("submit")[0].click()
        self.wait_for_page_change(add_facility_url)
        
        self.check_django_message(message_type="success", contains="has been successfully saved!")
