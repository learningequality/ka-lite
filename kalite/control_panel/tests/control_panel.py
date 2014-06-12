import time

from selenium.common.exceptions import NoSuchElementException

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import CreateFacilityMixin, CreateGroupMixin
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin


class FacilityControlTests(CreateFacilityMixin,
                           CreateAdminMixin,
                           CreateDeviceMixin,
                           KALiteDistributedBrowserTestCase):

    def test_delete_facility(self):
        self.setup_fake_device()
        facility_name = 'should-be-deleted'
        self.fac = self.create_facility(name=facility_name)
        self.browser_login_admin()
        self.browse_to(self.reverse('zone_redirect'))  # zone_redirect so it will bring us to the right zone

        # assert that our facility exists
        facility_row = self.browser.find_element_by_xpath('//tr[@facility-id="%s"]' % self.fac.id)
        facility_delete_link = facility_row.find_element_by_xpath('//a[@class="facility-delete-link"]/span')
        facility_delete_link.click()
        alert = self.browser.switch_to_alert()
        alert.accept()
        time.sleep(3)

        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_xpath('//tr[@facility-id="%s"]' % self.fac.id)
