from django.conf import settings
from django.core.urlresolvers import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from fle_utils.config.models import Settings

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.playlist import UNITS
from kalite.student_testing.api_resources import Test
from kalite.student_testing.models import TestLog
from kalite.testing.base import KALiteTestCase
from kalite.testing.client import KALiteClient
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin

from .utils import get_exam_mode_on, set_exam_mode_on, \
    get_current_unit_settings_value, set_current_unit_settings_value

logging = settings.LOG


class BaseTest(FacilityMixins, CreateDeviceMixin, KALiteTestCase):

    client_class = KALiteClient

    exam_id = 'g3_t1'  # needs to be the first exam in the test list UI
    login_url = reverse('login')
    logout_url = reverse('logout')
    test_list_url = reverse('test_list')
    exam_page_url = reverse('test', args=[exam_id])
    put_url = '/test/api/test/%s/' % exam_id

    def setUp(self):

        super(BaseTest, self).setUp()

        # make tests faster
        self.setup_fake_device()

        self.client.setUp()
        self.assertTrue(self.client.facility)
        self.assertTrue(self.client.teacher)
        self.assertTrue(self.client.student)

    def tearDown(self):
        self.logout()
        super(BaseTest, self).tearDown()

    def login_teacher(self):
        response = self.client.login_teacher()
        # check content for teacher
        text = "Coach Reports"
        self.assertContains(response, text)
        # browse to the test list page to populate the test cache
        response_tests = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response_tests.request['PATH_INFO'], self.test_list_url)
        return response

    def login_student(self, url='/'):
        response = self.client.login_student()
        if url == '/':
            self.assertTrue(self.client.is_logged_in())
        if url == self.exam_page_url:
            text = '<title>Take Test | KA Lite</title>'
            self.assertContains(response, text)
        return response

    def logout(self):
        self.client.get(self.logout_url)
        self.assertTrue(self.client.is_logged_out())

    def get_page_redirects_to_login_url(self, url):
        response = self.client.get(url, follow=True)
        text = "If you don't have a login, please"
        self.assertContains(response, text)
        self.assertEqual(response.request['PATH_INFO'], self.login_url)
        self.assertEqual(response.status_code, 200)
        return response


class CoreTests(BaseTest):

    def setUp(self):
        super(CoreTests, self).setUp()

    def tearDown(self):
        super(CoreTests, self).tearDown()

    def test_teacher_can_access_test_list_page(self):
        self.login_teacher()
        # try to browse the test list page as teacher
        response = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.test_list_url)

    def test_student_cannot_access_test_list_page(self):
        # make sure we don't have exam mode on
        set_exam_mode_on('')
        self.login_student()
        # any attempt to browse the test list page as student will redirect to login page
        self.get_page_redirects_to_login_url(self.test_list_url)

    def test_student_cannot_access_exam_page_if_not_exam_mode(self):
        # make sure we don't have exam mode on
        set_exam_mode_on('')
        self.login_student()
        # any attempt to browse the exam page as student will raise a 404
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_access_exam_pages(self):
        self.logout()
        # try to access an exam page as guest
        self.get_page_redirects_to_login_url(self.exam_page_url)
        # try to access the test list page as guest
        self.get_page_redirects_to_login_url(self.test_list_url)

    def test_teacher_toggle_exam_mode(self):
        data = {}
        set_exam_mode_on('')  # set exam mode
        self.login_teacher()
        self.client.get(self.put_url)  # this will fill the testcache
        self.client.put(self.put_url, data=data, content_type='application/json')  # set exam mode
        # check student access on exam mode
        self.login_student(url=self.exam_page_url)
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.exam_page_url)
        self.logout()

        # reset exam mode
        self.login_teacher()
        self.client.get(self.put_url)  # this will fill the testcache
        self.client.put(self.put_url, data=data, content_type='application/json')
        # check student access if not on exam mode
        self.login_student()
        # any attempt to browse the exam page as student will raise a 404
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_redirect_student_if_exam_mode(self):
        """
        Login as teacher, set exam mode, then check the student if student is redirected to the exam page.

        option 1. set exam mode by code
        option 2. set exam mode by client.put call
        """

        def _check_student_access_to_exam(url=None):
            if not url:
                url = reverse('test', args=[self.exam_id])
            self.assertEqual(get_exam_mode_on(), self.exam_id)

            # logged-in student must be redirected to the exam page
            resp = self.login_student(url)
            text = 'test_id: "%s"' % self.exam_id
            self.assertContains(resp, text)
            self.assertEqual(resp.request['PATH_INFO'], url)

        # option 1. set exam mode by code
        self.login_teacher()
        set_exam_mode_on(self.exam_id)
        _check_student_access_to_exam()

        # option 2. set exam mode by client.put call
        data = {}
        set_exam_mode_on('')  # reset exam mode
        self.login_teacher()
        self.client.get(self.put_url)  # this will fill the testcache
        self.client.put(self.put_url, data=data, content_type='application/json')  # set exam mode
        _check_student_access_to_exam()


class BrowserTests(BaseTest, KALiteDistributedBrowserTestCase):

    CSS_TEST_ROW_BUTTON = '.test-row-button'
    CSS_TEST_ROW_BUTTON_ON = '.test-row-button.btn-info'
    TEXT_ENABLE = 'Enable Exam Mode'
    TEXT_DISABLE = 'Disable Exam Mode'

    persistent_browser = True

    def setUp(self):

        # super(KALiteDistributedBrowserTestCase, self).setUp()
        super(BrowserTests, self).setUp()

        # MUST: We inherit from LiveServerTestCase, so make the urls relative to the host url
        # or use the KALiteTestCase.reverse() method.
        self.test_list_url = self.reverse('test_list')
        self.exam_page_url = self.reverse('test', args=[self.exam_id])
        self.put_url = '%s%s' % (self.live_server_url, self.put_url,)

    def tearDown(self):
        super(BrowserTests, self).tearDown()

    def login_teacher_in_browser(self):
        self.browser_login_teacher(username=self.client.teacher_data['username'],
                                   password=self.client.teacher_data['password'],
                                   facility_name=self.client.facility.name)

    def login_student_in_browser(self, expect_url=None, exam_mode_on=False):
        self.browser_login_student(username=self.client.student_data['username'],
                                   password=self.client.student_data['password'],
                                   facility_name=self.client.facility.name,
                                   exam_mode_on=exam_mode_on)

    def wait_for_element(self, by, elem):
        WebDriverWait(self.browser, 2).until(ec.element_to_be_clickable((by, elem)))

    def get_button(self, is_on=False):
        if is_on:
            self.wait_for_element(By.CSS_SELECTOR, self.CSS_TEST_ROW_BUTTON_ON)
            WebDriverWait(self.browser,1).until(ec.text_to_be_present_in_element(
                (By.CSS_SELECTOR, self.CSS_TEST_ROW_BUTTON_ON), self.TEXT_DISABLE))
            btn = self.browser.find_element_by_css_selector(self.CSS_TEST_ROW_BUTTON_ON)
            self.assertEqual(btn.text, self.TEXT_DISABLE)
        else:
            self.wait_for_element(By.CSS_SELECTOR, self.CSS_TEST_ROW_BUTTON)
            WebDriverWait(self.browser,1).until(ec.text_to_be_present_in_element(
                (By.CSS_SELECTOR, self.CSS_TEST_ROW_BUTTON), self.TEXT_ENABLE))
            btn = self.browser.find_element_by_css_selector(self.CSS_TEST_ROW_BUTTON)
            self.assertEqual(btn.text, self.TEXT_ENABLE)
        return btn

    def test_exam_mode(self):
        self.login_teacher_in_browser()

        # go to test list page and look for an exam
        self.browse_to(self.test_list_url)

        # enable exam mode
        btn = self.get_button(is_on=False)
        btn.click()

        # disable exam mode
        btn = self.get_button(is_on=True)
        btn.click()

        # enable exam mode again
        btn = self.get_button(is_on=False)
        btn.click()
        btn = self.get_button(is_on=True)

        # logout the teacher and login a student to check the exam redirect
        self.browser_logout_user()
        self.login_student_in_browser(expect_url=self.exam_page_url, exam_mode_on=True)

        # did student redirect to exam page?
        self.assertEqual(self.browser.current_url, self.exam_page_url)
        self.wait_for_element(By.ID, 'start-test')
        btn = self.browser.find_element_by_id('start-test')
        self.assertEqual(btn.text, 'Begin test')

        # logout the student then log the teacher back in to disable the exam mode
        self.browser_logout_user()
        self.login_teacher_in_browser()

        # go to test list page and look for the enabled exam
        self.browse_to(self.test_list_url)
        # disable exam mode
        btn = self.get_button(is_on=True)
        btn.click()
        btn = self.get_button(is_on=False)

        # logout the teacher and login a student to check the exam redirect
        self.browser_logout_user()
        self.login_student_in_browser()
        self.assertEqual(self.reverse("homepage"), self.browser.current_url)

    def test_exam_mode_shut_out(self):

        set_exam_mode_on(self.exam_id)

        self.login_student_in_browser(expect_url=self.exam_page_url, exam_mode_on=True)

        # Start the quiz to create a test log

        self.wait_for_element(By.ID, 'start-test')

        self.browser.find_element_by_id("start-test").click()

        # Answer one question

        self.wait_for_element(By.ID, 'check-answer-button')

        # Turn off the exam

        set_exam_mode_on('')

        self.browser.find_element_by_css_selector("input").click()

        self.browser.find_element_by_id("check-answer-button").click()

        testlog = TestLog.objects.get(user=self.client.student, test=self.exam_id)

        # Check that the Test Log is started, but not advanced.
        self.assertEqual(testlog.started, True)
        self.assertEqual(testlog.index, 0)

        # logout the student and login a teacher to check they can access the exam.
        self.browser_logout_user()
        self.login_teacher_in_browser()
        self.browse_to(self.exam_page_url)

        # Start the quiz to create a test log

        self.wait_for_element(By.ID, 'start-test')

        self.browser.find_element_by_id("start-test").click()

        testlog = TestLog.objects.get(user=self.client.student, test=self.exam_id)

        # Check that the Test Log is started.
        self.assertEqual(testlog.started, True)


class CurrentUnitTests(FacilityMixins, CreateDeviceMixin, KALiteTestCase):

    client_class = KALiteClient

    def setUp(self):

        super(CurrentUnitTests, self).setUp()

        # MUST: We inherit from LiveServerTestCase, so make the urls relative to the host url
        # or use the KALiteTestCase.reverse() method.
        self.login_url = self.reverse('login')
        self.logout_url = self.reverse('logout')
        self.current_unit_url = self.reverse('current_unit')

        # make tests faster
        self.setup_fake_device()

        self.client.setUp()
        self.assertTrue(self.client.facility)
        self.assertTrue(self.client.teacher)
        self.assertTrue(self.client.student)

    def tearDown(self):
        self.logout()
        super(CurrentUnitTests, self).tearDown()

    def _check_url(self, response, url):
        path = response.request['PATH_INFO']
        self.assertEqual(path, url[-1*len(path):])

    def login_teacher(self):
        response = self.client.login_teacher()
        # check content for teacher
        text = "Coach Reports"
        self.assertContains(response, text)
        # browse to the current unit page
        response_tests = self.client.get(self.current_unit_url, follow=True)
        self._check_url(response_tests, self.current_unit_url)
        # check the current unit page's content
        text = '<title>Current Unit | KA Lite</title>'
        self.assertContains(response_tests, text)
        return response

    def login_student(self, url='/'):
        response = self.client.login_student()
        if url == '/':
            self.assertTrue(self.client.is_logged_in())
        return response

    def logout(self):
        self.client.get(self.logout_url)
        self.assertTrue(self.client.is_logged_out())

    def test_teacher_can_access_current_unit_page(self):
        self.login_teacher()
        # try to browse the test list page as teacher
        response = self.client.get(self.current_unit_url, follow=True)
        self._check_url(response, self.current_unit_url)

    def test_student_cannot_access_current_unit_page(self):
        self.login_student()
        # try to browse the test list page as student
        response = self.client.get(self.current_unit_url, follow=True)
        self._check_url(response, self.login_url)

    def test_guest_cannot_access_current_unit_page(self):
        # try to browse the test list page as guest
        response = self.client.get(self.current_unit_url, follow=True)
        self._check_url(response, self.login_url)


class CurrentUnitBrowserTests(CurrentUnitTests, KALiteDistributedBrowserTestCase):

    CSS_CURRENT_UNIT_NEXT_BUTTON = '.current-unit-button.next'
    CSS_CURRENT_UNIT_PREV_BUTTON = '.current-unit-button.previous'
    CSS_CURRENT_UNIT_ACTIVE = 'span.current-unit-'
    NEXT = 'Next'
    PREV = 'Previous'

    persistent_browser = True

    def setUp(self):
        # super(KALiteDistributedBrowserTestCase, self).setUp()
        super(CurrentUnitBrowserTests, self).setUp()

    def tearDown(self):
        super(CurrentUnitBrowserTests, self).tearDown()

    def login_teacher_in_browser(self):
        self.browser_login_teacher(username=self.client.teacher_data['username'],
                                   password=self.client.teacher_data['password'],
                                   facility_name=self.client.facility.name)

    def wait_for_element(self, by, elem):
        WebDriverWait(self.browser, 10).until(ec.visibility_of_element_located((by, elem)))

    def get_button(self, is_next=True):
        if is_next:
            self.wait_for_element(By.CSS_SELECTOR, self.CSS_CURRENT_UNIT_NEXT_BUTTON)
            btn = self.browser.find_element_by_css_selector(self.CSS_CURRENT_UNIT_NEXT_BUTTON)
            self.assertEqual(btn.text, self.NEXT)
        else:
            self.wait_for_element(By.CSS_SELECTOR, self.CSS_CURRENT_UNIT_PREV_BUTTON)
            btn = self.browser.find_element_by_css_selector(self.CSS_CURRENT_UNIT_PREV_BUTTON)
            self.assertEqual(btn.text, self.PREV)
        return btn

    def test_current_unit_first(self):
        self.login_teacher_in_browser()

        # go to current unit page
        self.browse_to(self.current_unit_url)

        facility_id = self.client.facility.id

        # save the current unit at Settings
        unit = get_current_unit_settings_value(facility_id)

        # click next and test that Setting was incremented
        btn = self.get_button(is_next=True)
        btn.click()

        # wait until ajax call is done
        sel = "%s%s" % (self.CSS_CURRENT_UNIT_ACTIVE, unit + 1,)
        self.wait_for_element(By.CSS_SELECTOR, sel)

        unit_next = get_current_unit_settings_value(facility_id)
        self.assertNotEqual(unit, unit_next)

        # click previous and test that Setting was decremented
        btn = self.get_button(is_next=False)
        btn.click()

        # wait until ajax call is done
        sel = "%s%s" % (self.CSS_CURRENT_UNIT_ACTIVE, unit,)
        self.wait_for_element(By.CSS_SELECTOR, sel)

        unit_prev = get_current_unit_settings_value(facility_id)
        self.assertEqual(unit, unit_prev)

        # check that previous button is disabled
        btn = self.get_button(is_next=False)
        self.assertFalse(btn.is_enabled(), "Previous button must be disabled when current unit is on first.")

    def test_current_unit_last(self):
        self.login_teacher_in_browser()

        facility_id = self.client.facility.id

        # set to max units and check the previous and next buttons
        set_current_unit_settings_value(facility_id, max(UNITS))

        # go to current unit page
        self.browse_to(self.current_unit_url)

        # save the current unit at Settings
        unit = get_current_unit_settings_value(facility_id)

        # must have been successfully set to max unit
        self.assertEqual(max(UNITS), unit)

        # check that next button is disabled
        btn = self.get_button(is_next=True)
        self.assertFalse(btn.is_enabled(), "Next button must be disabled when current unit is on last.")

        # click previous and test that Setting was decremented
        btn = self.get_button(is_next=False)
        btn.click()

        # wait until ajax call is done
        sel = "%s%s" % (self.CSS_CURRENT_UNIT_ACTIVE, unit - 1,)
        self.wait_for_element(By.CSS_SELECTOR, sel)

        unit_prev = get_current_unit_settings_value(facility_id)
        self.assertNotEqual(unit, unit_prev)

        # click next and test that Setting was incremented
        btn = self.get_button(is_next=True)
        btn.click()

        # wait until ajax call is done
        sel = "%s%s" % (self.CSS_CURRENT_UNIT_ACTIVE, unit,)
        self.wait_for_element(By.CSS_SELECTOR, sel)

        unit_next = get_current_unit_settings_value(facility_id)
        self.assertEqual(unit, unit_next)