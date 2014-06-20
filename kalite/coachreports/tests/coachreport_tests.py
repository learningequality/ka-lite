from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.student_testing.models import TestLog
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateGroupMixin
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin


class TestReportTests(FacilityMixins,
                       CreateAdminMixin,
                       CreateDeviceMixin,
                       KALiteDistributedBrowserTestCase):

    def test_student_scores_display(self):
        """
        Test that we show results for a test if they exist, 
        and don't when they dont
        """
        test_log_defaults = {
            'test': 128, # this must be an actual exercise
            'index': '0',
            'complete': True,
            'started': True,
            'total_number': 4,
            'total_correct': 2,
        }
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.student1 = self.create_student(first_name="I", last_name="tested", username="yay", facility=self.facility)
        self.student2 = self.create_student(first_name="I", last_name="didn't", username="boo", facility=self.facility)
        self.test_log = TestLog(user=self.student1, **test_log_defaults)
        self.test_log.save()
        self.admin = self.create_admin()
        self.browser_login_admin()
        self.browse_to(self.reverse('test_view'))
        student_score = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[2]/td[1]').text
        self.assertTrue(student_score=='50.0%')
        empty_student = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr/td[1]').text
        self.assertTrue(empty_student=='')



