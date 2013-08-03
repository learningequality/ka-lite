"""
These will be run when you run "manage.py test [main].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test main --liveserver=localhost:8004-8010
".
"""
from selenium.common.exceptions import NoSuchElementException

from main.tests.browser_tests import KALiteDistributedWithFacilityBrowserTestCase
from securesync.models import Facility, FacilityGroup, FacilityUser


class TestTabularViewErrors(KALiteDistributedWithFacilityBrowserTestCase):
    """
    """

    # First, make sure that user 1 can only log in with user 1's email/password
    def test_no_groups(self):
        self.browser_login_admin()
        self.browse_to(url_name="tabular_view")
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, "No users found.", "Error message with no groups.")


    def test_groups_no_group_selected(self):
        FacilityGroup(name="Test Group", facility=self.facility).save()
        self.browser_login_admin()
        self.browse_to(url_name="tabular_view")
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, "Please select a group above.", "Error message with no group selected.")


    def test_groups_group_selected_no_topic_selected(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, "Please select a topic above.", "Error message with no topic selected.")


    def test_groups_group_selected_topic_selected_no_users(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, "No users found.", "Error message with no users available.")


    def test_users_out_of_group(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        FacilityUser(username="test_user", password="not-blank", facility=self.facility).save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, "No users found.", "Error message with no users available.")


    def test_success_with_group(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        FacilityUser(username="test_user", password="not-blank", facility=self.facility, group=group).save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('#error_message')


    def test_success_no_group(self):
        FacilityUser(username="test_user", password="not-blank", facility=self.facility).save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction")
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('#error_message')
