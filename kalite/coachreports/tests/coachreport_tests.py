import json

from django.conf import settings
logging = settings.LOG

from datetime import datetime, timedelta
from django.utils import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from kalite.main.models import AttemptLog
from kalite.testing.base import KALiteBrowserTestCase, KALiteTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.playlist_mixins import CreatePlaylistProgressMixin
from kalite.testing.mixins.securesync_mixins import CreateZoneMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin


class APIDropdownTests(FacilityMixins,
                       StudentProgressMixin,
                       BrowserActionMixins,
                       CreateZoneMixin,
                       CreateAdminMixin,
                       KALiteBrowserTestCase):

    def setUp(self):
        super(APIDropdownTests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

        self.api_facility_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility"})
        self.api_group_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "group"})
        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

    def test_facility_endpoint(self):
        self.client.login(username='admin', password='admin')
        facility_resp = json.loads(self.client.get("%s?zone_id=%s" % (self.api_facility_url, self.zone.id)).content)
        objects = facility_resp.get("objects")
        self.assertEqual(len(objects), 1, "API response incorrect")
        self.assertEqual(objects[0]["name"], "facility1", "API response incorrect")
        self.client.logout()

    def test_group_endpoint(self):
        self.client.login(username='admin', password='admin')
        group_resp = json.loads(self.client.get("%s?facility_id=%s" % (self.api_group_url, self.facility.id)).content)
        objects = group_resp.get("objects")
        self.assertEqual(len(objects), 2, "API response incorrect")
        self.assertEqual(objects[0]["name"], "group1", "API response incorrect")
        self.assertEqual(objects[1]["name"], "empty_group", "API response incorrect")
        self.client.logout()


class CoachNavigationTest(FacilityMixins,
                          StudentProgressMixin,
                          BrowserActionMixins,
                          CreateZoneMixin,
                          CreateAdminMixin,
                          KALiteBrowserTestCase,
                          KALiteTestCase):

    """
    TODO(cpauya): If there is only one facility/group, the "All" option must not show.
    TODO(cpauya): If there is an empty facility/group (no students assigned), that option must not show.
    """

    def setUp(self):
        """
        Sample data
            Facilities      Groups           Student
            -------------------------------------------
            facility1       group1-1         student1-1
                            group1-2         student1-2a
                            group1-2         student1-2b
                            group2-1         student2-1
            default                          student2-0
        """
        super(CoachNavigationTest, self).setUp()

        # setup default data
        self.facility = self.create_facility(name="facility1")
        self.group11 = self.create_group(name='group1-1', facility=self.facility)
        self.group12 = self.create_group(name='group1-2', facility=self.facility)
        self.group2 = self.create_group(name='group2', facility=self.facility)

        self.facility_name = "default"
        self.default_facility = self.create_facility(name=self.facility_name)

        self.student11 = self.create_student(first_name="first1-1", last_name="last1-1",
                                            username="s1-1",
                                            facility=self.default_facility)
        self.student12a = self.create_student(first_name="first1-2a", last_name="last1-2",
                                            username="s1-2a", group=self.group12, facility=self.facility)
        self.student12b = self.create_student(first_name="first1-2b", last_name="last1-2",
                                            username="s1-2b", group=self.group12, facility=self.facility)
        self.student21 = self.create_student(first_name="first1-1", last_name="last2-1",
                                            username="s2-1", group=self.group2, facility=self.facility)

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        # list of urls of all report types for the coach reports
        self.urls = [
            self.reverse('tabular_view'),
            self.reverse('scatter_view'),
            self.reverse('timeline_view'),
        ]

        #Student-Testing is only the feature of Nalanda.
        #So tests related coachreports would be available with nalanda only.
        #Reverse of test_view with argument won't be available unless Nalanda.
        if "nalanda" in settings.CONFIG_PACKAGE:
            self.urls.append(self.reverse('test_view'))

        self.browser_login_admin(**self.admin_data)

    def test_dropdown_all_facilities(self):

        def _check_dropdown_values(url, expected):
            self.browse_to(url)
            facility_select = self.browser_wait_for_element(css_selector="#facility-select")
            result = facility_select.find_elements_by_tag_name('option')
            result = [item.text for item in result]
            self.assertEqual(expected, result)

        expected = ['All', 'facility1', 'default']
        for url in self.urls:
            _check_dropdown_values(url, expected)

    def test_dropdown_one_facility(self):
        """
        Test options for the group dropdown if a facility is selected.

        Loops thru each url per report types and checks the group options.
        """
        for url in self.urls:
            self.browse_to(url)
            facility_select = self.browser.find_element_by_id("facility-select")
            facility_options = facility_select.find_elements_by_tag_name('option')

            def _check_group_options(facility_option, expected):
                facility_option.click()
                group_select = self.browser_wait_for_element(css_selector="#group-select")
                group_options = group_select.find_elements_by_tag_name('option')
                result = [group_option.text for group_option in group_options]
                self.assertEqual(expected, result)

            # select All option
            facility_option = facility_options[0]
            self.assertEqual("All", facility_option.text)
            expected = ['All', 'Ungrouped', 'group1-1', 'group1-2', 'group2']
            _check_group_options(facility_option, expected)

            # select facility1 option
            facility_option = facility_options[1]
            self.assertEqual("facility1", facility_option.text)
            expected = ['All', 'group1-1', 'group1-2', 'group2']
            _check_group_options(facility_option, expected)

            # select default option
            facility_option = facility_options[2]
            self.assertEqual("default", facility_option.text)
            expected = ['All', 'Ungrouped']
            _check_group_options(facility_option, expected)

    def test_all_facility_in_topic_dropdown(self):
        """
        Test all facility and its corresponding users in the topic dropdown functionality.
        """
        self.browse_to(self.reverse('tabular_view'))
        facility_select = self.browser.find_element_by_id("facility-select")
        facility_select.find_elements_by_tag_name('option')[0].click()
        topic_select = self.browser_wait_for_element(css_selector="#topic")
        topic_select.find_elements_by_tag_name('option')[1].click()
        self.browser.find_element_by_id("display-topic-report").click()
        expected = ['first1-1 last1-1', 'first1-2a last1-2', 'first1-2b last1-2', 'first1-1 last2-1']
        student_list = WebDriverWait(self.browser, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "student-name"))
        )
        result = [item.text for item in student_list]
        self.assertEqual(expected, result)

    def test_facility1_in_topic_dropdown(self):
        """
        Test facility1 and its corresponding users in the topic dropdown functionality.
        """
        self.browse_to(self.reverse('tabular_view'))
        facility_select = self.browser.find_element_by_id("facility-select")
        facility_select.find_elements_by_tag_name('option')[1].click()
        topic_select = self.browser_wait_for_element(css_selector="#topic")
        topic_select.find_elements_by_tag_name('option')[1].click()
        self.browser.find_element_by_id("display-topic-report").click()
        expected = ['first1-2a last1-2', 'first1-2b last1-2', 'first1-1 last2-1']
        student_list = WebDriverWait(self.browser, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "student-name"))
        )
        result = [item.text for item in student_list]
        self.assertEqual(expected, result)

    def test_default_in_topic_dropdown(self):
        """
        Test default and its corresponding ungroup users in the topic dropdown functionality.
        """
        self.browse_to(self.reverse('tabular_view'))
        facility_select = self.browser.find_element_by_id("facility-select")
        facility_select.find_elements_by_tag_name('option')[2].click()
        group_select = self.browser_wait_for_element(css_selector="#group-select")
        group_select.find_elements_by_tag_name('option')[1].click()
        topic_select = self.browser_wait_for_element(css_selector="#topic")
        topic_select.find_elements_by_tag_name('option')[1].click()
        self.browser.find_element_by_id("display-topic-report").click()
        expected = ['first1-1 last1-1']
        student_list = WebDriverWait(self.browser, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "student-name"))
        )
        result = [item.text for item in student_list]
        self.assertEqual(expected, result)


@unittest.skipUnless("nalanda" in settings.CONFIG_PACKAGE, "requires Nalanda")
class PlaylistProgressTest(FacilityMixins,
                           CreateAdminMixin,
                           CreatePlaylistProgressMixin,
                           BrowserActionMixins,
                           KALiteBrowserTestCase):

    def setUp(self):
        super(PlaylistProgressTest, self).setUp()
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.admin = self.create_admin()
        self.student = self.create_student()
        self.playlist = self.create_playlist_progress(user=self.student)

    def test_student_playlist_progress(self):
        self.browser_login_student(username=self.student.username, password="password", facility_name=self.facility.name)
        self.browse_to(self.reverse('account_management'))

        # Confirm high level progress appears
        progress_bar = self.browser_wait_for_element(css_selector='.progress-bar')
        # progress_bar_success = self.browser_wait_for_element(css_selector='.progress-bar-success')
        self.assertTrue(progress_bar, "Playlist progress rendering incorrectly.")

        # Trigger API call
        self.browser.find_elements_by_class_name('toggle-details')[0].click()

        # Confirm lower-level progress appears
        playlist_details = self.browser_wait_for_element(css_selector='.progress-block')
        self.assertTrue(playlist_details, "Didn't load details")


