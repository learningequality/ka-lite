"""
These will be run when you run "manage.py test [main].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test main --liveserver=localhost:8004-8010
".
"""

import logging
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import unittest

import settings
from securesync.models import Facility, FacilityGroup, FacilityUser
from utils.django_utils import call_command_with_output
from utils.testing import distributed_only, KALiteDistributedBrowserTestCase, KALiteRegisteredDistributedBrowserTestCase


@distributed_only
class DeviceUnregisteredTest(KALiteDistributedBrowserTestCase):
    """Validate all the steps of registering a device.
    
    Currently, only testing that the device is not registered works.
    """

    def test_device_unregistered(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """

        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browser.get(home_url) # Load page
        self.check_django_message(message_type="warning", contains="complete the setup.")
        self.assertFalse(self.is_logged_in(), "Not (yet) logged in")
        
        # Now, log in as admin
        self.login_admin()


@distributed_only
class ChangeLocalUserPassword(unittest.TestCase):
    """Tests for the changelocalpassword command"""
    
    def setUp(self):
        """Create a new facility and facility user"""
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
        """Change the password on an existing user."""
        
        # Now, re-retrieve the user, to check.
        (out,err,val) = call_command_with_output("changelocalpassword", self.user.username, noinput=True)
        self.assertEquals(err, "", "no output on stderr")
        self.assertNotEquals(out, "", "some output on stderr")
        self.assertEquals(val, 0, "Exit code is zero")

    def test_fail_change_password(self):
        """Fail to change the password on a nonexistent user."""
        fake_username = "fakeusername"
        
        (out,err,val) = call_command_with_output("changelocalpassword", fake_username, noinput=True)
        match = re.match(r"^.*Error: user '([^']+)' does not exist$", err.replace("\n",""), re.M)
        self.assertFalse(match is None, "could not parse stderr: (%s)" % err)
        self.assertEquals(match.groups()[0], fake_username, "Verify printed fake username")
        self.assertNotEquals(val, 0, "Verify exit code is non-zero")


@distributed_only
class UserRegistrationCaseTest(KALiteRegisteredDistributedBrowserTestCase):
    username   = "user1"
    password   = "password"

    def test_register_login_exact(self):
        """Tests that a user can login with the exact same email address as registered"""
         
        # Register user in one case
        self.register_user(username=self.username.lower(), password=self.password)

        # Login in the same case
        self.login_student(username=self.username.lower(), password=self.password)
        self.logout_user()

        
    def test_login_mixed(self):
        """Tests that a user can login with the uppercased version of the email address that was registered"""
         
        # Register user in one case
        self.register_user(username=self.username.lower(), password=self.password)

        # Login in the same case
        self.login_student(username=self.username.upper(), password=self.password)
        self.logout_user()
        

    def test_register_mixed(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""
         
        # Register user in one case
        self.register_user(username=self.username.lower(), password=self.password)

        # Try to register again in a different case
        self.register_user(username=self.username.upper(), password=self.password, expect_success=False)

        text_box = self.browser.find_element_by_id("id_username") # form element        
        error    = text_box.parent.find_elements_by_class_name("errorlist")[-1]
        self.assertIn("A user with this username at this facility already exists.", error.text, "Check 'username is taken' error.")


    def test_login_two_users_different_cases(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""
        
        user1_uname = self.username.lower()
        user2_uname = "a"+self.username.lower()
        user1_password = self.password
        user2_password = "a"+self.password
        user1_fname = "User1"
        user2_fname = "User2"
        
        # Register & activate two users with different usernames / emails
        self.register_user(username=user1_uname, password=user1_password, first_name=user1_fname)
        self.login_student(username=user1_uname, password=user1_password)
        self.logout_user()
        
        self.register_user(username=user2_uname, password=user2_password, first_name=user2_fname)
        self.login_student(username=user2_uname, password=user2_password)
        self.logout_user()
        
        # Change the second user to be a case-different version of the first user
        user2 = FacilityUser.objects.get(username=user2_uname)
        user2_uname = user1_uname.upper()
        user2.username = user2_uname
        user2.email = user2_uname
        user2.save()
        
        # First, make sure that user 1 can only log in with user 1's email/password
        self.login_student(username=user1_uname, password=user1_password) # succeeds
        self.logout_user()

        self.login_student(username=user2_uname, password=user1_password, expect_success=False) # fails
        self.assertFalse(self.is_logged_in(user2_uname), "make sure user2 is NOT logged in.")
        self.check_django_message("error", contains="There was an error logging you in.")

        # Now, check the same in the opposite direction.
        self.login_student(username=user2_uname, password=user2_password) # succeeds
        self.logout_user()

        self.login_student(username=user1_uname, password=user2_password, expect_success=False) # fails
        self.assertFalse(self.is_logged_in(user2_uname), "make sure user2 is NOT logged in.")
        self.check_django_message("error", contains="There was an error logging you in.")
