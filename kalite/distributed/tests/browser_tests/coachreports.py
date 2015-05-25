"""
Basic tests of coach reports, inside the browser
"""
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from kalite.facility.models import FacilityGroup, FacilityUser
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins


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

        self.url = self.reverse("coach_reports")

    def test_groups_group_selected_no_users(self):
        self.browser_login_admin(**self.admin_data)
        url = "%s%s/%s/" % (self.url, self.facility.id, self.group.id,)
        self.browse_to(url)
        try:
            button = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.ID, "show_tabular_report")))
            button.click()
            elem = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "alert-warning")))
            # Check if error message is contained in the alert bubble container.
            self.assertTrue("No learner accounts in this group have been created." in elem.text)
        except TimeoutException:
            self.fail("Didn't find the error message with no users available.")

    def test_success_with_group(self):
        fu = FacilityUser(username="test_user", facility=self.facility, group=self.group)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin(**self.admin_data)
        url = "%s%s/%s/" % (self.url, self.facility.id, self.group.id,)
        self.browse_to(url)
        button = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.ID, "show_tabular_report")))
        button.click()
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('.alert-danger')

    def test_success_no_group(self):
        fu = FacilityUser(username="test_user", facility=self.facility)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin(**self.admin_data)
        url = "%s%s/" % (self.url, self.facility.id,)
        self.browse_to(url)
        button = WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.ID, "show_tabular_report")))
        button.click()
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('.alert-danger')
