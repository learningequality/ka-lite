"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.webdriver.firefox.webdriver import WebDriver

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from django.utils.translation import ugettext as _

from fle_utils.django_utils import call_command_with_output
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.testing.browser import BrowserTestCase


class KALiteDistributedBrowserTestCase(BrowserTestCase):
    """Base class for distributed server test cases.
    They will have different functions in here, for sure.
    """

    default_username = "test_student"
    default_password = "socrates"
    default_facility_name = "middle of nowhere"

    def tearDown(self):
        """
        """

        # Must clean up, as browser sessions could persist
        if self.persistent_browser:
            self.browser_logout_user()
        super(KALiteDistributedBrowserTestCase, self).tearDown()

    def create_student(self, username=default_username, password=default_password, facility_name=default_facility_name):
        facilities = Facility.objects.filter(name=facility_name)
        facility = facilities[0] if facilities else self.create_facility()
        student = FacilityUser(username=username, facility=facility)
        student.set_password(raw_password=password)
        student.save()

        return student

    def create_facility(self, facility_name=default_facility_name):
        if Facility.objects.filter(name=facility_name):
            logging.debug("Creating duplicate facility: %s" % facility_name)
        facility = Facility(name=facility_name)
        facility.save()
        return facility

    def browser_register_user(self, username, password, first_name="firstname", last_name="lastname", facility_name=None, stay_logged_in=False, expect_success=True):
        """Tests that a user can register"""

        # Expected results vary based on whether a user is logged in or not.
        if not stay_logged_in:
            self.browser_logout_user()

        register_url = self.reverse("add_facility_student")
        self.browse_to(register_url) # Load page
        #self.assertIn(_("Sign up"), self.browser.title, "Register page title") # this depends on who is logged in.

        # Part 1: REGISTER
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)
        self.browser_activate_element(id="id_username") # explicitly set the focus, to start
        self.browser_form_fill(username) # first name
        self.browser_form_fill(first_name) # first name
        self.browser_form_fill(last_name) # last name
        self.browser_form_fill(password) #password
        self.browser_form_fill(password) #password (again)
        self.browser_form_fill(Keys.TAB) # skip language
        self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(reverse("login"), self.browser.current_url, "Register browses to login page" )
            #self.browser_check_django_message(message_type="success", contains="You successfully registered.")
            # uncomment message check when that code gets checked in

    def browser_login_user(self, username, password, facility_name=None, expect_success=True):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("login")
        self.browse_to(login_url) # Load page
        self.assertIn(_("Log in"), self.browser.title, "Login page title")

        # Focus should be on username, password and submit
        #   should be accessible through keyboard only.
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)

        self.browser.find_element_by_id("id_username").clear() # clear any data
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(password)
        self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            time.sleep(0.5)  # allow async status to update
            self.assertTrue(self.browser_is_logged_in(username), "make sure %s is logged in." % username)


    def browser_login_admin(self, username=None, password=None, expect_success=True):
        if username is None:
            username = self.admin_user.username
        if password is None:
            password = self.admin_pass

        self.browser_login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("zone_management", kwargs={"zone_id": "None"}), self.browser.current_url, "Login browses to zone_management page" )

    def browser_login_teacher(self, username, password, facility_name=None, expect_success=True):
        self.browser_login_user(username=username, password=password, facility_name=facility_name, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("coach_reports"), self.browser.current_url, "Login browses to coach reports page" )
            self.browser_check_django_message("success", contains="You've been logged in!")

    def browser_login_student(self, username, password, facility_name=None, expect_success=True):
        self.browser_login_user(username=username, password=password, facility_name=facility_name, expect_success=expect_success)
        time.sleep(self.max_wait_time/10) # allow time for async messages to load
        if expect_success:
            self.assertIn(reverse("homepage"), self.browser.current_url, "Login browses to homepage" )
            self.browser_check_django_message("success", contains="You've been logged in!")

    def browser_logout_user(self):
        if self.browser_is_logged_in():
            # Since logout redirects to the homepage, browse_to will fail (with no good way to avoid).
            #   so be smarter in that case.
            if self.reverse("homepage") in self.browser.current_url:
                self.browser.get(self.reverse("logout"))
            else:
                self.browse_to(self.reverse("logout"))
            self.assertIn(reverse("homepage"), self.browser.current_url, "Logout browses to homepage" )
            self.assertFalse(self.browser_is_logged_in(), "Make sure that user is no longer logged in.")

    def browser_is_logged_in(self, expected_username=None):
        # Two ways to be logged in:
        # 1. Student: #logged-in-name is username
        # 2. Admin: #logout contains username
        try:
            logged_in_name_text = self.browser.find_element_by_id("logged-in-name").text.strip()
            logout_text = self.browser.find_element_by_id("nav_logout").text.strip()
        except NoSuchElementException:
            # We're on an unrecognized webpage
            return False

        username_text = logged_in_name_text or logout_text[0:-len(" (%s)" % _("Logout"))]

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
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()

            user_obj = FacilityUser.objects.filter(username__iexact=expected_username)
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()
            else:
                assert username_text == "", "Impossible for anybody to be logged in."


class KALiteDistributedWithFacilityBrowserTestCase(KALiteDistributedBrowserTestCase):
    """
    Same thing, but do the setup steps to register a facility.
    """
    facility_name = 'middle of nowhere'

    def setUp(self):
        """Add a facility, so users can begin registering / logging in immediately."""
        super(KALiteDistributedWithFacilityBrowserTestCase,self).setUp() # sets up admin, etc
        self.facility = self.create_facility(facility_name=self.facility_name)

