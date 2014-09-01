import time

from selenium.common.exceptions import NoSuchElementException

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateGroupMixin
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin


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
        facility_row = self.browser.find_element_by_xpath('//tr[@facility-id="%s"]' % self.fac.id)
        facility_delete_link = facility_row.find_element_by_xpath('//a[@class="facility-delete-link"]/span')
        facility_delete_link.click()
        alert = self.browser.switch_to_alert()
        alert.send_keys("should-be-deleted")
        alert.accept()
        time.sleep(5)

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

        confirm_group_delete_button = self.browser.find_element_by_xpath('//button[contains(@class, "delete-group")]')
        confirm_group_delete_button.click()

        # there should be a confirm popup
        alert = self.browser.switch_to_alert()
        alert.accept()

        time.sleep(8)

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
