import time

from django.conf import settings
from django.utils import unittest
from django.test import Client

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateGroupMixin
from kalite.testing.mixins.student_testing_mixins import StudentTestingMixins
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin

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

        self.browser_click_and_accept('button.delete-group')

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//tr[@value="%s"]' % self.group.id)

    def test_teachers_have_no_group_delete_button(self):
        teacher_username, teacher_password = 'teacher1', 'password'
        self.teacher = self.create_teacher(username=teacher_username,
                                           password=teacher_password)
        self.browser_login_teacher(username=teacher_username,
                                   password=teacher_password,
                                   facility_name=self.teacher.facility.name)

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


class CSVExportTests(FacilityMixins,
                     StudentTestingMixins,
                     CreateDeviceMixin,
                     CreateAdminMixin,
                     KALiteDistributedBrowserTestCase):
    
    def setUp(self):
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.base_url = self.reverse("zone_data_export", kwargs={"zone_id": None})

        self.group = self.create_group(name='group1', facility=self.facility)
        self.empty_group = self.create_group(name='empty_group', facility=self.facility)

        self.stu1 = self.create_student(username='stu1', facility=self.facility, group=self.group)
        self.stu2 = self.create_student(username='stu2', facility=self.facility)

        self.test_log_1 = self.create_test_log(user=self.stu1)
        self.test_log_2 = self.create_test_log(user=self.stu2)

        self.admin = self.create_admin()
        self.client = Client()
        self.client.login(username='admin', password='admin')

        super(CSVExportTests, self).setUp()

    def test_export_all(self):
        resp = self.client.get(self.base_url + "?facility_id=all&group_id=all")
        self.assertEquals(len(resp._container), 4, "CSV file has wrong number of rows")
        first_row = resp._container[2].split(',')
        self.assertEquals(self.group.name, first_row[2], "Data is malformed")

    def test_export_grouped_students_only(self):
        resp = self.client.get(self.base_url + "?facility_id=all&group_id=%s" % self.group.id)
        self.assertEquals(len(resp._container), 3, "CSV file has wrong number of rows")
        first_row = resp._container[2].split(',')
        self.assertEquals(self.group.name, first_row[2], "Returned data for wrong group")
