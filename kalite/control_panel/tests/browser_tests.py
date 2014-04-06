"""
Basic tests of coach reports, inside the browser
"""
from selenium.common.exceptions import NoSuchElementException

from facility.models import Facility, FacilityGroup, FacilityUser
from main.tests.browser_tests import KALiteDistributedWithFacilityBrowserTestCase


class TestUserManagement(KALiteDistributedWithFacilityBrowserTestCase):
    """
    Test errors and successes for different user management actions.
    """

    def test_no_groups_no_users(self):
        self.browser_login_admin()
        self.browse_to(url_name="userlist")
        self.browser.find_element_by_css_selector('#selection-bar')
        self.assertContains(self.browser.find_element_by_css_selector('#selection-bar').text, "No Groups at this Facility", "Does not report no groups with no groups.")
        self.assertContains(self.browser.find_element_by_css_selector('#selection-bar').text, "No Users at this Facility", "Does not report no users with no users.")


    def test_groups_one_group_one_user_in_group_no_ungrouped_no_group_selected(self):
        facility_name = "Test Group"
        group = FacilityGroup(name=facility_name, facility=self.facility)
        group.save()
        user = FacilityUser(username="test_user", password="not-blank", facility=self.facility, group=group)
        user.save()
        self.browser_login_admin()
        self.browse_to(url_name="userlist")
        self.browser.find_element_by_css_selector('#selection-bar')
        self.assertNotContains(self.browser.find_element_by_css_selector('#selection-bar').text, "Please select a group above.", "Asks user to select group when only one group, and ungrouped is empty.")
        self.assertEqual(self.browser.find_element_by_css_selector('#group').text, "Test Group", "Allows user to select when only one group, and ungrouped is empty.")

    def remove_user_one_group_one_user_in_group_no_ungrouped_no_group_selected(self):
        facility_name = "Test Group"
        group = FacilityGroup(name=facility_name, facility=self.facility)
        group.save()
        username = "test_user"
        user = FacilityUser(username=username, password="not-blank", facility=self.facility, group=group)
        user.save()
        self.browser_login_admin()
        self.browse_to(url_name="userlist")
        self.browser.find_element_by_css_selector('input[value=%s]' % username).click()
        self.browser.find_element_by_id("removegroup").click()