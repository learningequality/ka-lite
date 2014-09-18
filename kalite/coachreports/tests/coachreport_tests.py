from datetime import datetime

from kalite.main.models import AttemptLog
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, CreatePlaylistProgressMixin, FacilityMixins, StudentProgressMixin


from kalite.student_testing.models import TestLog
from kalite.testing import KALiteTestCase


class TestReportTests(FacilityMixins,
                      StudentProgressMixin,
                      BrowserActionMixins,
                      CreateAdminMixin,
                      KALiteBrowserTestCase):

    def setUp(self):
        super(TestReportTests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

    def test_student_scores_display(self):
        """
        Test that we show results for a test if they exist,
        and don't when they dont
        """
        self.student1 = self.create_student(first_name="I", last_name="tested", username="yay", facility=self.facility)
        self.student2 = self.create_student(first_name="I", last_name="didn't", username="boo", facility=self.facility)
        self.test_log = self.create_test_log(user=self.student1)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('test_view'))
        student_score = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[2]/td[1]').text
        self.assertEqual(student_score[0:3], '10%')
        empty_student = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr/td[1]').text
        self.assertEqual(empty_student, '')

    def test_test_stats_display(self):
        """
        Test that we show correct stats for a test.
        """
        self.student1 = self.create_student(username="stu1", facility=self.facility)
        self.student2 = self.create_student(username="stu2", facility=self.facility)
        self.test_log1 = self.create_test_log(user=self.student1, total_number=4, total_correct=2)
        self.test_log2 = self.create_test_log(user=self.student2, total_number=4, total_correct=1)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('test_view'))
        stat_max = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[3]/td[1]').text
        self.assertEqual(stat_max, '10%')
        stat_min = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[4]/td[1]').text
        self.assertEqual(stat_min, '5%')
        stat_avg = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[5]/td[1]').text
        self.assertEqual(stat_avg, '7%')
        stat_std = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[6]/td[1]').text
        self.assertEqual(stat_std, '2%')

    def test_student_stats_display(self):
        """
        Test that we show correct stats for a test.
        """
        self.student1 = self.create_student(username="stu1", facility=self.facility)
        self.test_log1 = self.create_test_log(user=self.student1, total_number=4, total_correct=2)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('test_view'))
        stat_max = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[2]').text
        self.assertEqual(stat_max, '10%')
        stat_min = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[3]').text
        self.assertEqual(stat_min, '10%')
        stat_avg = self.browser.find_element_by_xpath('//div[@class="results-table"]/table/tbody/tr[1]/td[4]').text
        self.assertEqual(stat_avg, '10%')
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
        self.student1 = self.create_student(facility=self.facility)
        self.attempt_log = AttemptLog.objects.create(user=self.student1, **attempt_log_default)
        self.test_log = self.create_test_log(user=self.student1, total_number=5, total_correct=1)
        self.browser_login_admin(**self.admin_data)
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
        progress_bar_success = self.browser_wait_for_element(css_selector='.progress-bar-success')
        self.assertTrue(progress_bar_success, "Playlist progress rendering incorrectly.")
        self.assertTrue(progress_bar, "Playlist progress rendering incorrectly.")

        # Trigger API call
        self.browser.find_elements_by_class_name('toggle-details')[0].click()

        # Confirm lower-level progress appears
        playlist_details = self.browser_wait_for_element(css_selector='.progress-indicator-sm')
        self.assertTrue(playlist_details, "Didn't load details")
