"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.common.exceptions import TimeoutException, ElementNotVisibleException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import unittest
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateFacilityMixin

logging = settings.LOG


class TestAddFacility(BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase):
    """
    Test webpage for adding a facility
    """

    def test_browser_add_facility(self, facility_name="My Test Facility"):
        """Add a facility"""

        self.admin_data = {"username": "admin", "password": "admin"}
        self.create_admin(**self.admin_data)

        # Login as admin
        self.browser_login_admin(**self.admin_data)

        params = {
            "zone_id": None,
        }
        # Add the facility
        add_facility_url = self.reverse("add_facility", kwargs=params)
        self.browse_to(add_facility_url)

        self.browser_activate_element(id="id_name") # explicitly set the focus, to start
        self.browser_send_keys(facility_name)
        self.browser.find_elements_by_class_name("submit")[0].click()
        self.wait_for_page_change(add_facility_url)

        self.browser_check_django_message(message_type="success", contains="has been successfully saved!")


class DeviceUnregisteredTest(BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase):
    """Validate all the steps of registering a device.

    Currently, only testing that the device is not registered works.
    """

    def setUp(self):
        super(DeviceUnregisteredTest, self).setUp()
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

    @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    def test_device_unregistered(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """
        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browse_to(home_url) # Load page
        self.browser_check_django_message(message_type="warning", contains="complete the setup.")
        self.assertFalse(self.browser_is_logged_in(), "Not (yet) logged in")


@unittest.skipIf(settings.DISABLE_SELF_ADMIN, "Registration not allowed when DISABLE_SELF_ADMIN set.")
class UserRegistrationCaseTest(BrowserActionMixins, KALiteBrowserTestCase, CreateAdminMixin, CreateFacilityMixin):
    username = "user1"
    password = "password"

    def setUp(self):
        super(UserRegistrationCaseTest, self).setUp();
        self.create_admin()
        self.create_facility()

    def test_register_login_exact(self):
        """Tests that a user can login with the exact same email address as registered"""

        # Register user in one case
        self.browser_register_user(username=self.username.lower(), password=self.password)

        # Login in the same case
        self.browser_login_student(username=self.username.lower(), password=self.password)
        self.browser_logout_user()


class MainEmptyFormSubmitCaseTest(CreateAdminMixin, BrowserActionMixins, KALiteBrowserTestCase, CreateFacilityMixin):
    """
    Submit forms with no values, make sure there are no errors.

    Note: these are functions on securesync, but
    """

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

        super(MainEmptyFormSubmitCaseTest, self).setUp()
        self.browser_login_admin(**self.admin_data)

    def test_add_student_form(self):
        self.empty_form_test(url=self.reverse("add_facility_student"), submission_element_id="id_username")

    def test_add_teacher_form(self):
        self.empty_form_test(url=self.reverse("add_facility_teacher"), submission_element_id="id_username")

    def test_add_group_form(self):
        self.empty_form_test(url=self.reverse("add_group"), submission_element_id="id_name")


@override_settings(SESSION_IDLE_TIMEOUT=1)
class TestSessionTimeout(CreateAdminMixin, BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):
    """
    Test webpage for timing out user sessions
    """

    def test_admin_no_logout_after_interval(self):
        """Admin should not be auto-logged out"""
        admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**admin_data)
        self.browser_login_admin(**admin_data)
        time.sleep(3)
        self.browse_to(self.reverse("homepage"))
        self.assertTrue(self.browser_is_logged_in(), "Timeout should not logout admin")

    def test_teacher_no_logout_after_interval(self):
        """Teacher should not be auto-logged out"""
        self.teacher = self.create_teacher()
        self.browser_login_teacher(username=self.teacher.username, password="password")
        time.sleep(3)
        self.browse_to(self.reverse("homepage"))
        self.assertTrue(self.browser_is_logged_in(), "Timeout should not logout teacher")


class AlertsRemovedAfterNavigationTest(BrowserActionMixins, CreateAdminMixin, CreateFacilityMixin, KALiteBrowserTestCase):

    def setUp(self):
        super(AlertsRemovedAfterNavigationTest, self).setUp()
        self.create_admin()
        self.create_facility()
        self.browser_register_user(username="johnduck", password="superpassword")

    def test_login_alert_is_removed(self):
        self.browser_login_student(username="johnduck", password="superpassword")
        try:
            self.assertTrue(WebDriverWait(self.browser, 3).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR,"div.alert-dismissible"))
            ))
        except TimeoutException:
            self.fail("No alert present on page after login.")
        self.browse_to(self.reverse("learn"))
        try:
            self.assertTrue(WebDriverWait(self.browser, 3).until(
                expected_conditions.invisibility_of_element_located((By.CSS_SELECTOR,"div.alert-dismissible"))
            ))
        except TimeoutException:
            self.fail("Alert present on page after navigation event. Expected no alerts.")
