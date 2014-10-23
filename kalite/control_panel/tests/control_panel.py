import json

from django.conf import settings

from selenium.common.exceptions import NoSuchElementException

from kalite.testing.base import KALiteBrowserTestCase, KALiteClientTestCase, KALiteTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins, CreateZoneMixin, StudentProgressMixin, CreateAdminMixin

logging = settings.LOG


class FacilityControlTests(FacilityMixins,
                           CreateAdminMixin,
                           BrowserActionMixins,
                           KALiteBrowserTestCase):

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        super(FacilityControlTests, self).setUp()

    def test_delete_facility(self):
        facility_name = 'should-be-deleted'
        self.fac = self.create_facility(name=facility_name)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone

        selector = '.facility-delete-link'
        self.browser_click_and_accept(selector, text=facility_name)


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

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//a[@class="facility-delete-link"]')


class GroupControlTests(FacilityMixins,
                        CreateAdminMixin,
                        BrowserActionMixins,
                        KALiteBrowserTestCase):

    def setUp(self):
        self.facility = self.create_facility()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        group_name = 'group1'
        self.group = self.create_group(name=group_name, facility=self.facility)

        super(GroupControlTests, self).setUp()

    def test_delete_group(self):

        self.browser_login_admin(**self.admin_data)
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
                         CreateZoneMixin,
                         CreateAdminMixin,
                         KALiteTestCase):

    def setUp(self):
        super(CSVExportTestSetup, self).setUp()

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

        self.exercise_log_1 = self.create_exercise_log(user=self.stu1)
        self.exercise_log_2 = self.create_exercise_log(user=self.stu2)

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        # base urls
        self.distributed_data_export_url = "%s%s%s" % (self.reverse("data_export"), "?zone_id=", self.facility.get_zone().id)
        self.api_facility_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility"})
        self.api_group_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "group"})
        self.api_facility_user_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "facility_user_csv"})
        self.api_test_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "test_log_csv"})
        self.api_attempt_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "attempt_log_csv"})
        self.api_exercise_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "exercise_log_csv"})
        self.api_device_log_csv_url = self.reverse("api_dispatch_list", kwargs={"resource_name": "device_log_csv"})


class CSVExportAPITests(CSVExportTestSetup, KALiteClientTestCase):

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
        exercise_log_csv = json.loads(self.client.get(self.api_exercise_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(exercise_log_csv.get("objects"), "Authorization error")
        device_log_csv_resp = json.loads(self.client.get(self.api_device_log_csv_url + "?zone_id=" + self.zone.id).content)
        self.assertTrue(device_log_csv_resp.get("objects"), "Authorization error")
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
        exercise_log_csv = json.loads(self.client.get(self.api_exercise_log_csv_url + "?group_id=" + self.group.id).content)
        self.assertTrue(exercise_log_csv.get("objects"), "Authorization error")
        device_log_csv_resp = json.loads(self.client.get(self.api_device_log_csv_url + "?zone_id=" + self.zone.id).content)
        self.assertTrue(device_log_csv_resp.get("objects"), "Authorization error")
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
        exercise_log_csv = self.client.get(self.api_exercise_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(exercise_log_csv.content, "Authorization error")
        device_log_csv_resp = self.client.get(self.api_device_log_csv_url + "?zone_id=" + self.zone.id)
        self.assertFalse(device_log_csv_resp.get("objects"), "Authorization error")
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
        exercise_log_csv = self.client.get(self.api_exercise_log_csv_url + "?group_id=" + self.group.id)
        self.assertFalse(exercise_log_csv.content, "Authorization error")
        device_log_csv_resp = self.client.get(self.api_device_log_csv_url + "?zone_id=" + self.zone.id)
        self.assertFalse(device_log_csv_resp.get("objects"), "Authorization error")


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


    def test_device_log_csv_endpoint(self):
        # Test filtering by facility
        self.client.login(username='admin', password='admin')
        facility_filtered_resp = self.client.get(self.api_exercise_log_csv_url + "?facility_id=" + self.facility.id + "&format=csv").content
        rows = filter(None, facility_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 3, "API response incorrect")

        # Test filtering by group
        group_filtered_resp = self.client.get(self.api_exercise_log_csv_url + "?group_id=" + self.group.id + "&format=csv").content
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

    def test_device_log_csv_endpoint(self):
        # Test filtering by zone
        self.client.login(username='admin', password='admin')
        zone_filtered_resp = self.client.get(self.api_device_log_csv_url + "?zone_id=" + self.zone.id + "&format=csv").content
        rows = filter(None, zone_filtered_resp.split("\n"))
        self.assertEqual(len(rows), 2, "API response incorrect")


class CSVExportBrowserTests(CSVExportTestSetup, BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase):

    def setUp(self):
        super(CSVExportBrowserTests, self).setUp()

    def test_user_interface(self):
        self.browser_login_admin(**self.admin_data)
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
