import json
import time

from django.conf import settings
from django.utils import unittest
from django.test import Client

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from kalite.control_panel.views import UNGROUPED
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.testing import KALiteTestCase, KALiteClient
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateGroupMixin
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin, CreateZoneMixin

logging = settings.LOG


class FacilityControlTests(FacilityMixins,
                           CreateAdminMixin,
                           CreateDeviceMixin,
                           KALiteDistributedBrowserTestCase):

    def setUp(self):
        self.setup_fake_device()
        super(FacilityControlTests, self).setUp()

    def test_delete_facility(self):
        facility_name = 'should-be-deleted'
        self.fac = self.create_facility(name=facility_name)
        self.browser_login_admin()
        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone

        # assert that our facility exists
        selector = 'tr[facility-id="%s"] > td > a.facility-delete-link > span' % self.fac.id
        self.browser_click_and_accept(selector, text=facility_name)

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//tr[@facility-id="%s"]' % self.fac.id)

    def test_teachers_have_no_facility_delete_button(self):
        facility_name = 'should-not-be-deleted'
        self.fac = self.create_facility(name=facility_name)

        teacher_username, teacher_password = 'teacher1', 'password'
        self.teacher = self.create_teacher(username=teacher_username,
                                           password=teacher_password)
        self.browser_login_teacher(username=teacher_username,
                                   password=teacher_password,
                                   facility_name=self.teacher.facility.name)

        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone
        facility_row = self.browser.find_element_by_xpath('//tr[@facility-id="%s"]' % self.fac.id)

        with self.assertRaises(NoSuchElementException):
            facility_row.find_element_by_xpath('//a[@class="facility-delete-link"]')


class GroupControlTests(FacilityMixins,
                        CreateDeviceMixin,
                        KALiteDistributedBrowserTestCase):

    def setUp(self):
        self.setup_fake_device()
        self.facility = self.create_facility()

        group_name = 'group1'
        self.group = self.create_group(name=group_name, facility=self.facility)

        super(GroupControlTests, self).setUp()

    def test_delete_group(self):

        self.browser_login_admin()
        self.browse_to(self.reverse('facility_management', kwargs={'facility_id': self.facility.id, 'zone_id': None}))

        group_row = self.browser.find_element_by_xpath('//tr[@value="%s"]' % self.group.id)
        group_delete_checkbox = group_row.find_element_by_xpath('.//input[@type="checkbox" and @value="#groups"]')
        group_delete_checkbox.click()

        confirm_group_selector = ".delete-group"
        self.browser_click_and_accept(confirm_group_selector)

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//tr[@value="%s"]' % self.group.id)

    def test_teachers_have_no_group_delete_button(self):
        teacher_username, teacher_password = 'teacher1', 'password'
        self.teacher = self.create_teacher(username=teacher_username,
                                           password=teacher_password,
                                           facility=self.facility)
        self.browser_login_teacher(username=teacher_username,
                                   password=teacher_password,
                                   facility_name=self.facility.name)

        self.browse_to(self.reverse('facility_management', kwargs={'facility_id': self.facility.id, 'zone_id': None}))

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//button[@class="delete-group"]')

    def test_teachers_have_no_delete_coaches_button(self):
        teacher_username, teacher_password = 'teacher1', 'password'
        self.teacher = self.create_teacher(username=teacher_username,
                                           password=teacher_password,
                                           facility=self.facility)
        self.browser_login_teacher(username=teacher_username,
                                   password=teacher_password,
                                   facility_name=self.teacher.facility.name)

        self.browse_to(self.reverse('facility_management', kwargs={'facility_id': self.facility.id, 'zone_id': None}))

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//button[@id="delete-coaches"]')


class CSVExportTestSetup(FacilityMixins,
                     StudentProgressMixin,
                     CreateDeviceMixin,
                     CreateZoneMixin,
                     CreateAdminMixin,
                     KALiteDistributedBrowserTestCase):

    def setUp(self):
        self.setup_fake_device()
        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

        self.teacher = self.create_teacher(username="teacher", password="password", facility=self.facility)

        self.stu1 = self.create_student(username='stu1', facility=self.facility, group=self.group)
        self.stu2 = self.create_student(username='stu2', facility=self.facility)

        self.test_log_1 = self.create_test_log(user=self.stu1)
        self.test_log_2 = self.create_test_log(user=self.stu2)

        self.attempt_log_1 = self.create_attempt_log(user=self.stu1)
        self.attempt_log_2 = self.create_attempt_log(user=self.stu2)

        self.admin = self.create_admin()

        # base urls
        self.distributed_data_export_url = "%s%s%s" % (self.reverse("data_export"), "?zone_id=", self.facility.get_zone().id)
        self.api_facility_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility"})
        self.api_group_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "group"})
        self.api_facility_user_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility_user_csv"})
        self.api_test_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "test_log_csv"})
        self.api_attempt_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "attempt_log_csv"})

        super(CSVExportTestSetup, self).setUp()


class CSVExportAPITests(CSVExportTestSetup, KALiteTestCase):
    
    def setUp(self):
        self.client = KALiteClient()
        super(CSVExportAPITests, self).setUp()

    def test_api_auth_super_admin(self):
        # Super admin can access everything 
        self.client.login(username='admin', password='admin')
        facility_resp = json.loads(self.client.get(self.api_facility_url).content)
        self.assertTrue(facility_resp.get("objects"), "Authorization error")
        group_resp = json.loads(self.client.get(self.api_group_url + "?facility_id=" + self.facility.id).content)
        self.assertTrue(group_resp.get("objects"), "Authorization error")
        user_csv_resp = json.loads(self.client.get(self.api_facility_user_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(user_csv_resp.get("objects"), "Authorization error")
        attempt_log_csv_resp = json.loads(self.client.get(self.api_attempt_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(attempt_log_csv_resp.get("objects"), "Authorization error")
        test_log_csv_resp = json.loads(self.client.get(self.api_test_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(test_log_csv_resp.get("objects"), "Authorization error")
        self.client.logout()

    def test_api_auth_teacher(self):
        # Teacher can access everything on zone
        self.client.login(username='teacher', password='password', facility=self.facility.id)
        facility_resp = json.loads(self.client.get(self.api_facility_url).content)
        self.assertTrue(facility_resp.get("objects"), "Authorization error")
        group_resp = json.loads(self.client.get(self.api_group_url + "?facility_id=" + self.facility.id).content)
        self.assertTrue(group_resp.get("objects"), "Authorization error")
        user_csv_resp = json.loads(self.client.get(self.api_facility_user_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(user_csv_resp.get("objects"), "Authorization error")
        attempt_log_csv_resp = json.loads(self.client.get(self.api_attempt_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(attempt_log_csv_resp.get("objects"), "Authorization error")
        test_log_csv_resp = json.loads(self.client.get(self.api_test_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(test_log_csv_resp.get("objects"), "Authorization error")
        self.client.logout()

    def test_api_auth_student(self):
        # Student can't
        self.client.login(username='stu1', password='password', facility=self.facility.id)
        facility_resp = self.client.get(self.api_facility_url)
        self.assertFalse(facility_resp.content, "Authorization error")
        group_resp = self.client.get(self.api_group_url + "?facility_id=" + self.facility.id)
        self.assertFalse(group_resp.content, "Authorization error")
        user_csv_resp = self.client.get(self.api_facility_user_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(user_csv_resp.content, "Authorization error")
        attempt_log_csv_resp = self.client.get(self.api_attempt_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(attempt_log_csv_resp.content, "Authorization error")
        test_log_csv_resp = self.client.get(self.api_test_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(test_log_csv_resp.content, "Authorization error")
        self.client.logout()

    def test_api_auth_not_logged_in(self):
        # Not logged in can't 
        facility_resp = self.client.get(self.api_facility_url)
        self.assertFalse(facility_resp.content, "Authorization error")
        group_resp = self.client.get(self.api_group_url + "?facility_id=" + self.facility.id)
        self.assertFalse(group_resp.content, "Authorization error")
        user_csv_resp = self.client.get(self.api_facility_user_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(user_csv_resp.content, "Authorization error")
        attempt_log_csv_resp = self.client.get(self.api_attempt_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(attempt_log_csv_resp.content, "Authorization error")
        test_log_csv_resp = self.client.get(self.api_test_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(test_log_csv_resp.content, "Authorization error")


    def test_facility_endpoint(self):
        self.client.login(username='admin', password='admin')
        facility_resp = json.loads(self.client.get(self.api_facility_url + "?zone_id=" + self.zone.id).content)
        objects = facility_resp.get("objects")
        self.assertEqual(len(objects), 1, "API response incorrect")
        self.assertEqual(objects[0]["name"], "facility1", "API response incorrect")
        self.client.logout()

    def test_group_endpoint(self):
        self.client.login(username='admin', password='admin')
        group_resp = json.loads(self.client.get(self.api_group_url + "?facility_id=" + self.facility.id).content)
        objects = group_resp.get("objects")
        self.assertEqual(len(objects), 2, "API response incorrect")
        self.assertEqual(objects[0]["name"], "group1", "API response incorrect")
        self.assertEqual(objects[1]["name"], "empty_group", "API response incorrect")
        self.client.logout()

    def test_facility_user_csv_endpoint(self):
        # Test filtering by facility
        self.client.login(username='admin', password='admin')
        facility_filtered_resp = self.client.get(self.api_facility_user_csv_url + "?facility_id=" + self.facility.id + "&format=csv").content
        rows = filter(None, facility_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 4, "API response incorrect")

        # Test filtering by group
        group_filtered_resp = self.client.get(self.api_facility_user_csv_url + "?group_id=" + self.group.id + "&format=csv").content
        rows = filter(None, group_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 2, "API response incorrect")
        self.client.logout()


    def test_test_log_csv_endpoint(self):
        # Test filtering by facility
        self.client.login(username='admin', password='admin')
        facility_filtered_resp = self.client.get(self.api_test_log_csv_url + "?facility_id=" + self.facility.id + "&format=csv").content
        rows = filter(None, facility_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 3, "API response incorrect")

        # Test filtering by group
        group_filtered_resp = self.client.get(self.api_test_log_csv_url + "?group_id=" + self.group.id + "&format=csv").content
        rows = filter(None, group_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 2, "API response incorrect")
        self.client.logout()


    def test_attempt_log_csv_endpoint(self):
        # Test filtering by facility
        self.client.login(username='admin', password='admin')
        facility_filtered_resp = self.client.get(self.api_attempt_log_csv_url + "?facility_id=" + self.facility.id + "&format=csv").content
        rows = filter(None, facility_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 3, "API response incorrect")

        # Test filtering by group
        group_filtered_resp = self.client.get(self.api_attempt_log_csv_url + "?group_id=" + self.group.id + "&format=csv").content
        rows = filter(None, group_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 2, "API response incorrect")
        self.client.logout()


class CSVExportBrowserTests(CSVExportTestSetup):

    def setUp(self):
        super(CSVExportBrowserTests, self).setUp()

    def test_user_interface(self):
        self.browser_login_admin() 
        self.browse_to(self.distributed_data_export_url)

        self.browser_wait_for_ajax_calls_to_finish()

        # Check that group is disabled until facility is selected
        group_select = self.browser.find_element_by_id("group-name")
        self.assertFalse(group_select.is_enabled(), "UI error")
        
        # Select facility, wait, and ensure group is enabled
        facility_select = self.browser.find_element_by_id("facility-name")
        for option in facility_select.find_elements_by_tag_name('option'):
            if option.text == 'facility1':
                option.click() # select() in earlier versions of webdriver
                break

        self.browser_wait_for_ajax_calls_to_finish()

        # Check that group is enabled now
        group_select = self.browser.find_element_by_id("group-name")
        self.assertTrue(group_select.is_enabled(), "UI error")

        # Click and make sure something happens
        # note: not actually clicking the download since selenium cannot handle file save dialogs
        export = self.browser.find_element_by_id("export-button")
        self.assertTrue(export.is_enabled(), "UI error")
