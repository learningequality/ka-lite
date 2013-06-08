"""
These will be run when you run "manage.py test [main].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test main --liveserver=localhost:8004-8010
".
"""

import logging
import unittest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from django.test import TestCase
from django.core.urlresolvers import reverse

import settings
from utils.testing import main_only, KALiteLocalBrowserTestCase, add_to_local_settings

@main_only
class DeviceUnregisteredTest(KALiteLocalBrowserTestCase):
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
        

    
@main_only
class DeviceAutoregisterTest(KALiteLocalBrowserTestCase):
    """"""
    
    def setUp(self):
        add_to_local_settings("INSTALL_CERTIFICATES", ["dummy_certificate"])
        super(DeviceAutoregisterTest,self).setUp()
    
    def tearDown(self):
        #import pdb; pdb.set_trace()
        #pass
        super(DeviceAutoregisterTest,self).tearDown()
        
    @unittest.skipIf(settings.CENTRAL_SERVER, "")
    def test_device_registration(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")


@main_only
class ChangeLocalUserPassword(unittest.TestCase):
    def setUp(self):
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.group = FacilityGroup(facility=self.facility, name="Test Class")
        self.group.full_clean()
        self.group.save()
        self.user = FacilityUser(facility=self.facility, username="testuser", first_name="Firstname", last_name="Lastname", group=self.group)
        self.user.clear_text_password = "testpass" # not used anywhere but by us, for testing purposes
        self.user.set_password(self.user.clear_text_password)
        self.user.full_clean()
        self.user.save()
    
    
    def test_change_password(self):
        
        # Now, re-retrieve the user, to check.
        (out,err,val) = call_command_with_output("changelocalpassword", self.user.username, noinput=True)
        self.assertEquals(err, "", "no output on stderr")
        self.assertNotEquals(out, "", "some output on stderr")
        self.assertEquals(val, 0, "Exit code is zero")
        
        match = re.match(r"^.*Generated new password for user '([^']+)': '([^']+)'", out.replace("\n",""), re.MULTILINE)
        self.assertFalse(match is None, "could not parse stdout")

        user = FacilityUser.objects.get(facility=self.facility, username=self.user.username)
        self.assertEquals(user.username, match.groups()[0], "Username reported correctly")

        self.assertTrue(user.check_password(match.groups()[1]), "New password works")
        self.assertFalse(user.check_password(self.user.clear_text_password), "NOT the old password")
        

    def test_no_user(self):
        fake_username = self.user.username + "xxxxx"
        
        #with self.assertRaises(FacilityUser.DoesNotExist):
        (out,err,val) = call_command_with_output("changelocalpassword", fake_username, noinput=True)

        self.assertNotIn("Generated new password for user", out, "Did not set password")
        self.assertNotEquals(err, "", "some output on stderr")

        match = re.match(r"^.*Error: user '([^']+)' does not exist$", err.replace("\n",""), re.M)
        self.assertFalse(match is None, "could not parse stderr")
        self.assertEquals(match.groups()[0], fake_username, "Verify printed fake username")
        self.assertNotEquals(val, 0, "Verify exit code is non-zero")
