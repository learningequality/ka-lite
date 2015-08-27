import json

from django.conf import settings
from django.test.utils import override_settings

from selenium.common.exceptions import NoSuchElementException

from kalite.testing.base import KALiteBrowserTestCase, KALiteClientTestCase, KALiteTestCase

from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.securesync_mixins import CreateZoneMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging = settings.LOG


class DeviceRegistrationTests(FacilityMixins,
                       StudentProgressMixin,
                       BrowserActionMixins,
                       CreateZoneMixin,
                       CreateAdminMixin,
                       KALiteBrowserTestCase):

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        super(DeviceRegistrationTests, self).setUp()


    def test_device_registration_availability(self):
        """
        This test simulate the device registration availability.
        The Registration button must appear else the test will fail.
        """
        facility_name = 'default'
        self.fac = self.create_facility(name=facility_name)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone
        element = self.browser.find_element_by_id('not-registered')
        try:
             WebDriverWait(self.browser, 0.7).until(EC.visibility_of(element))
        except TimeoutException:
             pass
        self.assertTrue(element.is_displayed())


    def test_device_already_register(self):
        """
        This test will simulate the device that has already registered and the only option is available is update
        the software else the test will fail.
        """
        facility_name = 'default'
        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.fac = self.create_facility(name=facility_name)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone
        element = self.browser.find_element_by_id('force-sync')
        try:
             WebDriverWait(self.browser, 0.7).until(EC.visibility_of(element))
        except TimeoutException:
            pass
        self.assertTrue(element.is_displayed())


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

    def test_checkbox_not_autocompleted(self):
        # This is a regression test for issue #2929
        # Firefox aggressively autocompletes form elements, meaning if a checkbox is checked
        # upon page refresh, it will stay checked. This then disrupts our checkbox/highlight
        # UI and makes them desynchronized.
        # N.B. This assumes that our browser tests are running on Firefox, otherwise, this test is moot.
        self.browser_login_admin(**self.admin_data)

        self.browse_to(self.reverse('facility_management', kwargs={'facility_id': self.facility.id, 'zone_id': None}))

        group_row = self.browser.find_element_by_xpath('//tr[@value="%s"]' % self.group.id)
        group_delete_checkbox = group_row.find_element_by_xpath('.//input[@type="checkbox" and @value="#groups"]')
        group_delete_checkbox.click()

        self.browser.refresh()

        self.assertNotEqual(self.browser.find_element_by_xpath('.//input[@type="checkbox" and @value="#groups"]').get_attribute("checked"), u'true')


@override_settings(RESTRICTED_TEACHER_PERMISSIONS=True)
class RestrictedTeacherTests(FacilityMixins,
                             BrowserActionMixins,
                             KALiteClientTestCase,
                             KALiteBrowserTestCase):

    def setUp(self):
        super(RestrictedTeacherTests, self).setUp()

        self.teacher_username, self.teacher_password = "teacher", "password"
        self.facility = self.create_facility()
        self.student = self.create_student(facility=self.facility)
        self.teacher = self.create_teacher(username=self.teacher_username,
                                           password=self.teacher_password,
                                           facility=self.facility)

    def test_teacher_cant_edit_facilities(self):
        facility_to_edit = self.create_facility(name="edit me")

        self.browser_login_teacher(username=self.teacher_username,
                                   password=self.teacher_password,
                                   facility_name=self.facility.name)

        # subtest for making sure they don't see the create facility button
        self.browse_to(self.reverse("facility_management", kwargs={"zone_id": None, "facility_id": facility_to_edit.id}))
        elem = self.browser.find_element_by_css_selector('a.edit-facility')
        self.assertEquals(elem.value_of_css_property("display"), "none", "edit-facility is still displayed!")

        # TODO(aron): move these client test cases to their own test class
        # subtest for making sure they can't actually load the create facility page
        # use the django client since it's faster
        self.client.login_teacher(data={"username": self.teacher_username,
                                        "password": self.teacher_password},
                                  facility=self.facility)
        resp = self.client.get(self.reverse("facility_form", kwargs={"facility_id": facility_to_edit.id}))
        self.assertEqual(resp.status_code, 403, "Teacher was still authorized to delete facilities; status code is %s" % resp.status_code)

    def test_teacher_cant_create_facilities(self):
        self.browser_login_teacher(username=self.teacher_username,
                                   password=self.teacher_password,
                                   facility_name=self.facility.name)

        # subtest for making sure they don't see the create facility button
        self.browse_to(self.reverse("zone_management", kwargs={"zone_id": None}))
        elem = self.browser.find_element_by_css_selector('a.create-facility')
        self.assertEquals(elem.value_of_css_property("display"), "none", "delete-facility is still displayed!")

        # TODO(aron): move these client test cases to their own test class
        # subtest for making sure they can't actually load the create facility page
        # use the django client since it's faster
        self.client.login_teacher(data={"username": self.teacher_username,
                                        "password": self.teacher_password},
                                  facility=self.facility)
        resp = self.client.get(self.reverse("add_facility", kwargs={"zone_id": None}))
        self.assertEqual(resp.status_code, 403, "Teacher was still authorized to delete facilities; status code is %s" % resp.status_code)

    def test_teacher_cant_create_students(self):
        self.browser_login_teacher(username=self.teacher_username,
                                   password=self.teacher_password,
                                   facility_name=self.facility.name)

        # subtest for making sure they don't see the create student button
        self.browse_to(self.reverse("facility_management", kwargs={"zone_id": None, "facility_id": self.facility.id}))
        elem = self.browser.find_element_by_css_selector('a.create-student')
        self.assertEquals(elem.value_of_css_property("display"), "none", "create-student is still displayed!")

        # TODO(aron): move these client test cases to their own test class
        # subtest for making sure they can't actually load the create facility page
        # use the django client since it's faster
        self.client.login_teacher(data={"username": self.teacher_username,
                                        "password": self.teacher_password},
                                  facility=self.facility)
        resp = self.client.get(self.reverse("add_facility_student"))
        self.assertEqual(resp.status_code, 403, "Teacher was still authorized to create students; status code is %s" % resp.status_code)

    def test_teacher_can_edit_students(self):
        self.browser_login_teacher(username=self.teacher_username,
                                   password=self.teacher_password,
                                   facility_name=self.facility.name)

        # NOTE: Hi all, we disabled this test since we want nalanda
        # teachers to still edit students, mainly so they can reset
        # the password.

        # # subtest for making sure they don't see the edit student button
        self.browse_to(self.reverse("facility_management", kwargs={"zone_id": None, "facility_id": self.facility.id}))
        student_row = self.browser.find_element_by_xpath('//tr[@value="%s"]' % self.student.id)

        # # make sure we render the link
        student_row.find_element_by_css_selector("a.edit-student")

        # TODO(aron): move these client test cases to their own test class
        # subtest for making sure they can't actually load the create facility page
        # use the django client since it's faster
        self.client.login_teacher(data={"username": self.teacher_username,
                                        "password": self.teacher_password},
                                  facility=self.facility)
        resp = self.client.get(self.reverse("edit_facility_user", kwargs={"facility_user_id": self.student.id}))
        self.assertEqual(resp.status_code, 200, "Teacher was not authorized to edit students; status code is %s" % resp.status_code)

    def test_teacher_cant_delete_students(self):
        self.browser_login_teacher(username=self.teacher_username,
                                   password=self.teacher_password,
                                   facility_name=self.facility.name)

        # subtest for making sure they don't see the delete student button
        self.browse_to(self.reverse("facility_management", kwargs={"zone_id": None, "facility_id": self.facility.id}))

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_css_selector("div.delete-student")


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

        self.assertEqual(len(facility_select.find_elements_by_tag_name('option')), 2, "Invalid Number of Facilities")

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

    def test_user_interface_teacher(self):
        teacher_username, teacher_password = 'teacher1', 'password'
        self.teacher = self.create_teacher(username=teacher_username,
                                           password=teacher_password)
        self.browser_login_teacher(username=teacher_username,
                                   password=teacher_password,
                                   facility_name=self.teacher.facility.name)
        self.browse_to(self.distributed_data_export_url)

        # Why is this here? Is the intention to wait for the page to load?
        #self.browser_wait_for_ajax_calls_to_finish()

        facility_select = self.browser.find_element_by_id("facility-name")
        self.assertFalse(facility_select.is_enabled(), "UI error")

        for option in facility_select.find_elements_by_tag_name('option'):
            if option.text == self.teacher.facility.name:
                self.assertTrue(option.is_selected(), "Invalid Facility Selected")
                break

        # self.browser_wait_for_ajax_calls_to_finish()

        # Check that group is enabled now
        group_select = self.browser.find_element_by_id("group-name")
        self.assertTrue(group_select.is_enabled(), "UI error")

        # Click and make sure something happens
        # note: not actually clicking the download since selenium cannot handle file save dialogs
        export = self.browser.find_element_by_id("export-button")
        self.assertTrue(export.is_enabled(), "UI error")
