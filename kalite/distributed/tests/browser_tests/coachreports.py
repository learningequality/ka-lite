"""
Basic tests of coach reports, inside the browser
"""
from selenium.common.exceptions import NoSuchElementException

from django.utils.translation import ugettext as _

from .base import KALiteDistributedWithFacilityBrowserTestCase
from kalite.facility.models import Facility, FacilityGroup, FacilityUser


class TestTabularViewErrors(KALiteDistributedWithFacilityBrowserTestCase):
    """
    In the tabular view, certain scenarios will cause different errors to occur.  Test them here.
    """

    def test_no_groups_no_topic_selected(self):
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction")
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, _("No student accounts have been created."), "Error message with no users available, no topic selected.")


    def test_no_groups_with_topic_selected(self):
        self.browser_login_admin()
        self.browse_to(url_name="tabular_view")
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, _("Please select a topic above."), "Error message with no users available, no topic selected.")


    def test_groups_group_selected_no_topic_selected(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, _("Please select a topic above."), "Error message with no topic selected.")


    def test_groups_group_selected_topic_selected_no_users(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, _("No student accounts in this group have been created."), "Error message with no users available.")


    def test_users_out_of_group(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        fu = FacilityUser(username="test_user", facility=self.facility)  # Ungrouped
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        self.browser.find_element_by_css_selector('#error_message')
        self.assertEqual(self.browser.find_element_by_css_selector('#error_message').text, _("No student accounts in this group have been created."), "Error message with no users available.")


    def test_success_with_group(self):
        group = FacilityGroup(name="Test Group", facility=self.facility)
        group.save()
        fu = FacilityUser(username="test_user", facility=self.facility, group=group)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction&group=" + group.id)
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('#error_message')


    def test_success_no_group(self):
        fu = FacilityUser(username="test_user", facility=self.facility)
        fu.set_password(raw_password="not-blank")
        fu.save()
        self.browser_login_admin()
        self.browse_to(self.reverse("tabular_view") + "?topic=addition-subtraction")
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector('#error_message')
