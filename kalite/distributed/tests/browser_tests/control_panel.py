"""
Basic tests of coach reports, inside the browser
"""
import time
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from distributed.tests.browser_tests import KALiteDistributedWithFacilityBrowserTestCase
from facility.models import Facility, FacilityGroup, FacilityUser
from securesync.devices.models import Device, Zone


class TestUserManagement(KALiteDistributedWithFacilityBrowserTestCase):
    """
    Test errors and successes for different user management actions.
    """

    def test_no_groups_no_users(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        self.browser_login_admin()
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_css_selector('div#coaches p.no-data').text, "You currently have no coaches for this facility.", "Does not report no coaches with no coaches.")
        self.assertEqual(self.browser.find_element_by_css_selector('div#groups p.no-data').text, "No Groups at this Facility", "Does not report no groups with no groups.")
        self.assertEqual(self.browser.find_element_by_css_selector('div#students p.no-data').text, "You currently have no student data available.", "Does not report no users with no users.")

    def test_groups_one_group_no_user_in_group_no_ungrouped_no_group_selected(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        group_name = "Test Group"
        group = FacilityGroup(name=group_name, facility=self.facility)
        group.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr/td[1]").text, "Test Group", "Does not show group in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr/td[3]").text, "0", "Does not report zero users for empty group.")



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
        self.browser_login_admin()
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr/td[1]").text, "Test Group", "Does not show group in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr/td[3]").text, "1", "Does not report one user for group.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='students']/table/tbody/tr/td[1]").text, "test_user", "Does not show user in list.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='students']/table/tbody/tr/td[3]").text, "Test Group", "Does not report user in group.")


    def test_groups_two_groups_one_user_in_group_no_ungrouped_group_selected_move(self):
        facility = self.facility
        params = {
            "zone_id": None,
            "facility_id": facility.id,
        }
        group_name_1 = "From Group"
        group1 = FacilityGroup(name=group_name_1, facility=self.facility)
        group1.save()
        group_name_2 = "To Group"
        group2 = FacilityGroup(name=group_name_2, facility=self.facility)
        group2.save()
        user = FacilityUser(username="test_user", facility=self.facility, group=group1)
        user.set_password(raw_password="not-blank")
        user.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("facility_management", kwargs=params))
        self.browser.find_element_by_xpath("//div[@id='students']/table/tbody/tr/td[4]").click()
        Select(self.browser.find_element_by_css_selector("div#students select.movegrouplist")).select_by_visible_text("To Group")
        self.browser.find_element_by_css_selector("div#students button.movegroup").click()
        try:
            alert = self.browser.switch_to_alert()
        except NoAlertPresentException:
            alert = None
        self.assertNotEqual(alert, None, "Does not produce alert of group movement.")
        self.assertEqual(alert.text, "You are about to move selected users to another group.", "Does not warn that users are about to be moved.")
        self.browser.switch_to_alert().accept()

        time.sleep(2)
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr[1]/td[3]").text, "0", "Does not report no user for From Group.")
        self.assertEqual(self.browser.find_element_by_xpath("//div[@id='groups']/table/tbody/tr[2]/td[3]").text, "1", "Does not report one user for To Group.")