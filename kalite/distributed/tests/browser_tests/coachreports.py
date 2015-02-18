"""
Basic tests of coach reports, inside the browser
"""
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from kalite.facility.models import FacilityGroup, FacilityUser
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, FacilityMixins


class TestTabularViewErrors(BrowserActionMixins, CreateAdminMixin, FacilityMixins, KALiteBrowserTestCase):
    """
    In the tabular view, certain scenarios will cause different errors to occur.  Test them here.
    """

    def setUp(self):
        super(TestTabularViewErrors, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        self.facility = self.create_facility()

        self.group = FacilityGroup(name="Test Group", facility=self.facility)
        self.group.save()

        self.url = self.reverse("tabular_view")
        self.topic = "addition-subtraction"

    def test_no_groups_no_topic_selected(self):
        self.browser_login_admin(**self.admin_data)
        url = "%s?topic=%s" % (self.url, self.topic,)
        self.browse_to(url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("No learner accounts in this group have been created." in elem.text)
        except TimeoutException:
            self.fail("Error message for 'no group selected' is not found.")

    def test_no_groups_with_topic_selected(self):
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("Please select a topic." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with no users available, no topic selected.")

    def test_groups_group_selected_no_topic_selected(self):
        self.browser_login_admin(**self.admin_data)
        url = "%s?group_id=%s" % (self.url, self.group.id,)
        self.browse_to(url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("Please select a topic." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with no topic selected.")

    def test_groups_group_selected_topic_selected_no_users(self):
        self.browser_login_admin(**self.admin_data)
        url = "%s?topic=%s&group_id=%s" % (self.url, self.topic, self.group.id,)
        self.browse_to(url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("No learner accounts in this group have been created." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with no users available.")

    def test_groups_group_selected_topic_and_playlist_selected(self):
        self.browser_login_admin(**self.admin_data)
        url = "%s?group_id=%s&topic=%s&playlist=%s" % (self.reverse("tabular_view"),
                                                       self.group.id,
                                                       self.topic,
                                                       "test-playlist")
        self.browse_to(url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("Please select a topic." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with both topic and playlist selected.")

    def test_users_out_of_group(self):

        fu = FacilityUser(username="test_user", facility=self.facility)  # Ungrouped
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin(**self.admin_data)
        url = "%s?topic=%s&group_id=%s" % (self.url, self.topic, self.group.id,)
        self.browse_to(url)
        try:
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("No learner accounts in this group have been created." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with users out of group.")

    def test_success_with_group(self):
        fu = FacilityUser(username="test_user", facility=self.facility, group=self.group)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin(**self.admin_data)
        url = "%s?topic=%s&group_id=%s" % (self.url, self.topic, self.group.id,)
        self.browse_to(url)
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('.alert-danger')

    def test_success_no_group(self):
        fu = FacilityUser(username="test_user", facility=self.facility)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin(**self.admin_data)
        url = "%s?topic=%s" % (self.url, self.topic,)
        self.browse_to(url)
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('.alert-danger')
