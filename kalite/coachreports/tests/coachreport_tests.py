from datetime import datetime

from kalite.main.models import AttemptLog
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.student_testing.models import TestLog
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.student_progress_mixins import StudentProgressMixin
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin


class TestReportTests(FacilityMixins,
                      StudentProgressMixin,
                      CreateAdminMixin,
                      CreateDeviceMixin,
                      KALiteDistributedBrowserTestCase):

    def test_student_scores_display(self):
        """
        Test that we show results for a test if they exist,
        and don't when they dont
        """
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.student1 = self.create_student(first_name="I", last_name="tested", username="yay", facility=self.facility)
        self.student2 = self.create_student(first_name="I", last_name="didn't", username="boo", facility=self.facility)
        self.test_log = self.create_test_log(user=self.student1)
        self.admin = self.create_admin()
        self.browser_login_admin()
        self.browse_to(self.reverse('test_view'))
        student_score = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[2]/td[1]').text
        self.assertEqual(student_score[0:3], '50%')
        empty_student = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr/td[1]').text
        self.assertEqual(empty_student, '')

    def test_test_stats_display(self):
        """
        Test that we show correct stats for a test.
        """
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.student1 = self.create_student(username="stu1", facility=self.facility)
        self.student2 = self.create_student(username="stu2", facility=self.facility)
        self.test_log1 = self.create_test_log(user=self.student1, total_number=4, total_correct=2)
        self.test_log2 = self.create_test_log(user=self.student2, total_number=4, total_correct=1)
        self.admin = self.create_admin()
        self.browser_login_admin()
        self.browse_to(self.reverse('test_view'))
        stat_max = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[3]/td[1]').text
        self.assertEqual(stat_max, '50%')
        stat_min = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[4]/td[1]').text
        self.assertEqual(stat_min, '25%')
        stat_avg = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[5]/td[1]').text
        self.assertEqual(stat_avg, '37%')
        stat_std = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[6]/td[1]').text
        self.assertEqual(stat_std, '12%')

    def test_student_stats_display(self):
        """
        Test that we show correct stats for a test.
        """
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.student1 = self.create_student(username="stu1", facility=self.facility)
        self.test_log1 = self.create_test_log(user=self.student1, total_number=4, total_correct=2)
        self.admin = self.create_admin()
        self.browser_login_admin()
        self.browse_to(self.reverse('test_view'))
        stat_max = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[2]').text
        self.assertEqual(stat_max, '50%')
        stat_min = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[3]').text
        self.assertEqual(stat_min, '50%')
        stat_avg = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[4]').text
        self.assertEqual(stat_avg, '50%')
        stat_std = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[5]').text
        self.assertEqual(stat_std, '0%')

    def test_student_detail_scores_display(self):
        """
        Test that we show results for an exercise cluster in the test detail view
        """
        attempt_log_default = {
            'exercise_id': 'place_value',  # this must exist inside of the test
            'context_type': 'test',
            'context_id': 'g3_t1',
            'timestamp': datetime.now(),
            'correct': True,
        }
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.student1 = self.create_student(facility=self.facility)
        self.attempt_log = AttemptLog.objects.create(user=self.student1, **attempt_log_default)
        self.test_log = self.create_test_log(user=self.student1, total_number=5, total_correct=1)
        self.admin = self.create_admin()
        self.browser_login_admin()
        self.browse_to(self.reverse('test_detail_view', kwargs={'test_id': self.test_log.test}))
        student_score = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[3]').text
        self.assertEqual(student_score[0:4], '100%')
        stat_max = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[2]/td[3]').text
        self.assertEqual(stat_max[0:4], '100%')
        stat_min = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[3]/td[3]').text
        self.assertEqual(stat_min[0:4], '100%')
        stat_avg = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[4]/td[3]').text
        self.assertEqual(stat_avg[0:4], '100%')
        stat_std = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[5]/td[3]').text
        self.assertEqual(stat_std, '0%')
        overall = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[5]').text
        self.assertEqual(overall[0:4], '100%')
