from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from kalite.student_testing.models import TestLog
from kalite.testing.client import KALiteClient
from kalite.testing.base import KALiteClientTestCase, KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins, CreateTeacherMixin, CreateStudentMixin

from .utils import get_exam_mode_on, set_exam_mode_on

logging = settings.LOG


class BaseTest(FacilityMixins, KALiteClientTestCase):

    client_class = KALiteClient

    exam_id = 'g4_u401_t1'  # needs to be the first exam in the test list UI
    login_url = reverse('login')
    logout_url = reverse('logout')
    test_list_url = reverse('test_list')
    exam_page_url = reverse('test', args=[exam_id])
    put_url = '/test/api/test/%s/' % exam_id

    def setUp(self):

        super(BaseTest, self).setUp()

        self.facility = self.create_facility(name="facility1")
        self.teacher_data = CreateTeacherMixin.DEFAULTS.copy()
        self.student_data = CreateStudentMixin.DEFAULTS.copy()
        self.teacher_data['facility'] = self.student_data['facility'] = self.facility

        self.teacher = self.create_teacher(**self.teacher_data)
        self.student = self.create_student(**self.student_data)

    def tearDown(self):
        self.logout()
        super(BaseTest, self).tearDown()

    def login_teacher(self):
        response = self.client.login_teacher(data=self.teacher_data, facility=self.facility)
        # check content for teacher
        text = "Coach Reports"
        self.assertContains(response, text)
        # browse to the test list page to populate the test cache
        response_tests = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response_tests.request['PATH_INFO'], self.test_list_url)
        return response

    def login_student(self, url='/'):
        response = self.client.login_student(data=self.student_data, facility=self.facility)
        if url == '/':
            self.assertTrue(self.client.is_logged_in())
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


class BrowserTests(BrowserActionMixins, BaseTest, KALiteBrowserTestCase):

    CSS_TEST_ROW_BUTTON = '.test-row-button'
    CSS_TEST_ROW_BUTTON_ON = '.test-row-button.btn-info'
    TEXT_ENABLE = 'Enable Exam Mode'
    TEXT_DISABLE = 'Disable Exam Mode'

    def setUp(self):

        # super(KALiteBrowserTestCase, self).setUp()
        super(BrowserTests, self).setUp()

        # MUST: We inherit from LiveServerTestCase, so make the urls relative to the host url
        # or use the KALiteTestCase.reverse() method.
        self.test_list_url = self.reverse('test_list')
        self.exam_page_url = self.reverse('test', args=[self.exam_id])
        self.put_url = '%s%s' % (self.live_server_url, self.put_url,)

    def tearDown(self):
        super(BrowserTests, self).tearDown()

    def login_teacher_in_browser(self):
        self.browser_login_teacher(username=self.teacher_data['username'],
                                   password=self.teacher_data['password'],
                                   facility_name=self.facility.name)

    def login_student_in_browser(self, expect_url=None, exam_mode_on=False, browser=None):
        browser = browser or self.browser
        self.browser_login_student(username=self.student_data['username'],
                                   password=self.student_data['password'],
                                   facility_name=self.facility.name,
                                   exam_mode_on=exam_mode_on,
                                   browser=browser)

    def wait_for_element(self, by, elem, browser=None):
        browser = browser or self.browser
        WebDriverWait(browser, 5).until(ec.element_to_be_clickable((by, elem)))

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
        # Enable an exam as a teacher
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

        # Do not logout teacher (because this disables exams)
        # Instead, create a new browser instance and check the student redirects
        self.student_browser = self.create_browser()
        self.login_student_in_browser(expect_url=self.exam_page_url, exam_mode_on=True, browser=self.student_browser)

        # did student redirect to exam page?
        self.assertEqual(self.student_browser.current_url, self.exam_page_url)
        self.wait_for_element(By.ID, 'start-test', browser=self.student_browser)
        btn = self.student_browser.find_element_by_id('start-test')
        self.assertEqual(btn.text, 'Begin test')

        # Logout teacher to disable exam
        self.browser_logout_user()

        # Logout and login student to check exam redirect no longer in place
        self.browser_logout_user(browser=self.student_browser)
        self.login_student_in_browser(browser=self.student_browser)
        self.assertEqual(self.reverse("homepage"), self.student_browser.current_url)
        self.student_browser.quit()

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Passes locally but fails on travis")
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

        try:
            testlog = TestLog.objects.get(user=self.student, test=self.exam_id)
        except:
            pass

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
        testlog = TestLog.objects.get(user=self.student, test=self.exam_id)

        # Check that the Test Log is started.
        self.assertEqual(testlog.started, True)

    def exam_off_on_teacher_logout(self):
        self.login_teacher_in_browser()
        set_exam_mode_on(self.exam_id)
        self.assertEqual(get_exam_mode_on(), self.exam_id)
        self.browser_logout_user()
        self.assertEqual(get_exam_mode_on(), '')

    def exam_enabled_on_student_logout(self):
        self.login_student_in_browser()
        set_exam_mode_on(self.exam_id)
        self.assertEqual(get_exam_mode_on(), self.exam_id)
        self.browser_logout_user()
        self.assertEqual(get_exam_mode_on(), self.exam_id)
