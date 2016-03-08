"""
Basic tests of control panel, inside the browser
"""
import os
import mock
import urllib

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import Select, WebDriverWait

from django.conf import settings
from django.utils import unittest
from django.core.management import call_command

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.facility.models import FacilityGroup, FacilityUser
from kalite.i18n.base import get_installed_language_packs, set_default_language


@unittest.skipIf(getattr(settings, 'HEADLESS', None), "Doesn't work on HEADLESS.")
class TestUserManagement(BrowserActionMixins, CreateAdminMixin, FacilityMixins, KALiteBrowserTestCase):
    """
    Test errors and successes for different user management actions.
    """

    def setUp(self):
        super(TestUserManagement, self).setUp()
        self.facility_name = "fac"
        self.facility = self.create_facility(name=self.facility_name)
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

    def test_no_groups_no_users(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_css_selector('div#coaches p.no-data').text, "You currently have no coaches for this facility.", "Does not report no coaches with no coaches.")
        self.assertEqual(self.browser.find_element_by_css_selector('div#groups p.no-data').text, "You currently have no group data available.", "Does not report no groups with no groups.")
        self.assertEqual(self.browser.find_element_by_css_selector('div#students p.no-data').text, "You currently have no learner data available.", "Does not report no users with no users.")

    def test_groups_one_group_no_user_in_group_no_ungrouped_no_group_selected(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        group_name = "Test Group"
        group = FacilityGroup(name=group_name, facility=self.facility)
        group.save()
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[2]/a[1]").text, "Test Group", "Does not show group in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[5]").text, "0", "Does not report zero users for empty group.")

    def test_groups_one_group_one_user_in_group_no_ungrouped_no_group_selected(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        group_name = "Test Group"
        group = FacilityGroup(name=group_name, facility=self.facility)
        group.save()
        user = FacilityUser(username="test_user", facility=self.facility, group=group)
        user.set_password(raw_password="not-blank")
        user.save()
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[2]/a[1]").text.strip()[:len(group.name)], "Test Group", "Does not show group in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[5]").text.strip()[:len(group.name)], "1", "Does not report one user for group.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='students']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[2]").text.strip()[:len(user.username)], "test_user", "Does not show user in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='students']/div[@class='col-md-12']/div[@class='table-responsive']/table/tbody/tr/td[5]").text.strip()[:len(user.group.name)], "Test Group", "Does not report user in group.")


    def test_ungrouped_number_displays_correctly(self):
        """
        Ungrouped # of students wasn't displaying correctly, see: https://github.com/learningequality/ka-lite/pull/2230
        In particular it seems to have only occurred when a non-english language was set, so this test tried to
        mock a language pack download
        """
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
            "group_id": "Ungrouped"
        }
        # Login as admin
        self.browser_login_admin(**self.admin_data)

        self.register_device()

        user = FacilityUser(username="test_user", facility=self.facility, group=None)
        user.set_password(raw_password="not-blank")
        user.save()

        self.browse_to(self.reverse("group_management", kwargs=params))
        element = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='groups']/div/dl/dd"))
                )
        self.assertEqual(element.text, "1", "Does not report one user for group.")
