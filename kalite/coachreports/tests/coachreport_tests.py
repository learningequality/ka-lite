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
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, CreatePlaylistProgressMixin, CreateZoneMixin, \
    FacilityMixins, StudentProgressMixin


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


class TimelineReportTests(FacilityMixins,
                          StudentProgressMixin,
                          BrowserActionMixins,
                          CreateAdminMixin,
                          KALiteBrowserTestCase):
    def setUp(self):
        super(TimelineReportTests, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

    def test_user_interface(self):
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('timeline_view'))
        self.student1 = self.create_student(first_name="I", last_name="tested", username="yay", facility=self.facility)
        self.student2 = self.create_student(first_name="I", last_name="didn't", username="boo", facility=self.facility)
        self.browser.find_element_by_xpath('//button[@id="display-coach-report"]')


class TestScatterReport(FacilityMixins,
                        StudentProgressMixin,
                        BrowserActionMixins,
                        CreateAdminMixin,
                        KALiteBrowserTestCase):
    def setUp(self):
        super(TestScatterReport, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()

    def test_data_chart(self):
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('scatter_view'))
        self.student1 = self.create_student(first_name="I", last_name="tested", username="yay", facility=self.facility)
        self.student2 = self.create_student(first_name="I", last_name="didn't", username="boo", facility=self.facility)
        # check if all facility is selected
        facility_select = self.browser.find_element_by_id("facility-select")
        facility_options = facility_select.find_elements_by_tag_name('option')
        facility_option = facility_options[0]
        self.assertEqual("All", facility_option.text)
        # check if the xaxis is mastery and yaxis is effort
        datepicker_start = self.browser.find_element_by_id("datepicker_start")
        datepicker_end = self.browser.find_element_by_id("datepicker_end")

        now = datetime.now()
        current_date = datetime.now() - timedelta(days=31)
        self.assertEqual(current_date.strftime("%Y-%m-%d"), datepicker_start.get_attribute("value"))
        self.assertEqual(now.strftime("%Y-%m-%d"), datepicker_end.get_attribute("value"))

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


@unittest.skipUnless("nalanda" in settings.CONFIG_PACKAGE, "requires Nalanda")
class SpendingReportTests(FacilityMixins,
                          CreateAdminMixin,
                          BrowserActionMixins,
                          KALiteBrowserTestCase):

    def setUp(self):
        super(SpendingReportTests, self).setUp()
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()
        self.student = self.create_student()
        self.store_transaction = self.create_store_transaction_log(user=self.student)

    def test_spending_report_displays(self):
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('spending_report_view'))
        points_remaining = self.browser.find_element_by_xpath("//tbody/tr/td[2]")
        self.assertEqual(points_remaining.text, '-1000', "Remaining points incorrect; remainings points are actually %s" % points_remaining.text)

    def test_spending_report_detail_displays(self):
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse('spending_report_detail_view', kwargs={"user_id": self.student.id}))
        item_title = self.browser.find_element_by_xpath("//tbody/tr/td[2]")
        self.assertEqual(item_title.text, 'Alpha Chisel Marker', "Item title incorrect; item is actually %s" % item_title.text)
        item_cost = self.browser.find_element_by_xpath("//tbody/tr/td[4]")
        self.assertEqual(item_cost.text, '1000', "Item cost incorrect; item is actually %s" % item_cost.text)
