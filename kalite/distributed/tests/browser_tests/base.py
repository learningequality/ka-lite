"""
These use a web-browser, along selenium, to simulate user actions.
"""
import time

from django.conf import settings
from django.utils.translation import ugettext as _

from selenium.common.exceptions import NoSuchElementException

from kalite.facility.models import Facility, FacilityUser
from kalite.testing.browser import BrowserTestCase

logging = settings.LOG


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

    def create_student(self, username=default_username, password=default_password,
                       facility_name=default_facility_name):
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

    def browser_wait_for_ajax_calls_to_finish(self):
        while True:
            num_ajax_calls = int(self.browser.execute_script('return jQuery.active;'))
            if num_ajax_calls > 0:
                time.sleep(1)
            else:
                break

    def browser_register_user(self, username, password, first_name="firstname", last_name="lastname",
                              facility_name=None, stay_logged_in=False, expect_success=True):
        """Tests that a user can register"""

        # Expected results vary based on whether a user is logged in or not.
        if not stay_logged_in:
            self.browser_logout_user()

        register_url = self.reverse("add_facility_student")
        self.browse_to(register_url)  # Load page
        #self.assertIn(_("Sign up"), self.browser.title, "Register page title") # this depends on who is logged in.

        # Part 1: REGISTER
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)
        self.browser_activate_element(id="id_username")  # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(first_name)
        self.browser_form_fill(last_name)
        self.browser_form_fill(password)
        self.browser_form_fill(password)  # password (again)
        self.browser.find_element_by_id("id_username").submit()

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(self.reverse("login"), self.browser.current_url, "Register browses to login page")
            #self.browser_check_django_message(message_type="success", contains="You successfully registered.")
            # uncomment message check when that code gets checked in

    def browser_login_user(self, username, password, facility_name=None, expect_success=True):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("login")
        self.browse_to(login_url)  # Load page
        # self.assertIn(_("Log in"), self.browser.title, "Login page title")

        # Focus should be on username, password and submit
        #   should be accessible through keyboard only.
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element(id="id_facility")
            self.browser_send_keys(facility_name)

        self.browser.find_element_by_id("id_username").clear()  # clear any data
        self.browser.find_element_by_id("id_username").click()  # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(password)
        self.browser.find_element_by_id("id_username").submit()
        # self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            time.sleep(0.5)  # allow async status to update
            self.assertTrue(self.browser_is_logged_in(username), "make sure %s is logged in." % username)

    def browser_login_admin(self, username=None, password=None, expect_success=True, expect_url=None):
        if username is None:
            username = self.admin_user.username
        if password is None:
            password = self.admin_pass

        self.browser_login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(self.reverse("zone_management", kwargs={"zone_id": "None"}), self.browser.current_url,
                          "Login browses to zone_management page")

    def browser_login_teacher(self, username, password, facility_name=None, expect_success=True, expect_url=None):
        self.browser_login_user(username=username, password=password, facility_name=facility_name,
                                expect_success=expect_success)
        if expect_success:
            if not expect_url:
                expect_url = self.reverse("coach_reports")
            self.assertEqual(self.browser.current_url, expect_url)
            self.browser_check_django_message("alert-success", contains="You've been logged in!")

    def browser_login_student(self, username, password, facility_name=None, expect_success=True, expect_url=None,
                              exam_mode_on=False):
        """
        Consider that student may be redirected to the exam page when Settings.EXAM_MODE_ON is set.
        """
        self.browser_login_user(username=username, password=password, facility_name=facility_name,
                                expect_success=expect_success)
        if expect_success:
            if not expect_url:
                expect_url = self.reverse("homepage")
            self.assertEqual(self.browser.current_url, expect_url)
            if exam_mode_on:
                has_elem = self.browser_wait_for_element("#start-test")
                self.assertTrue(has_elem)
            else:
                self.browser_check_django_message("alert-success", contains="You've been logged in!")

    def browser_logout_user(self):
        if self.browser_is_logged_in():
            # Since logout redirects to the homepage, browse_to will fail (with no good way to avoid).
            #   so be smarter in that case.
            homepage_url = self.reverse("homepage")
            logout_url = self.reverse("logout")
            if homepage_url == self.browser.current_url:
                self.browser.get(logout_url)
            else:
                self.browse_to(logout_url)
            self.assertEqual(homepage_url, self.browser.current_url, "Logout redirects to the homepage")
            self.assertFalse(self.browser_is_logged_in(), "Make sure that user is no longer logged in.")

    def browser_is_logged_in(self, expected_username=None):
        # Two ways to be logged in:
        # 1. Student: #logged-in-name is username
        # 2. Admin: #logout contains username
        try:
            sitepoints_text = self.browser.find_element_by_id("sitepoints").text.strip()
            logout_text = self.browser.find_element_by_id("nav_logout").text.strip()
        except NoSuchElementException:
            # We're on an unrecognized webpage
            return False

        if sitepoints_text.startswith("Welcome, "):
            logged_in_name = sitepoints_text[len("Welcome, "):sitepoints_text.index("!")].strip()
        elif "|" in sitepoints_text:
            logged_in_name = sitepoints_text[:sitepoints_text.index("|")].strip()
        else:
            logged_in_name = None

        username_text = logged_in_name or logout_text[0:-len(" (%s)" % _("Logout"))]

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
        super(KALiteDistributedWithFacilityBrowserTestCase, self).setUp()  # sets up admin, etc
        self.facility = self.create_facility(facility_name=self.facility_name)
