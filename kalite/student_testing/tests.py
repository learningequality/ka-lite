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

logging = settings.LOG


class BaseTest(FacilityMixins, KALiteClientTestCase):

    client_class = KALiteClient

    exam_id = 'g4_ut1'  # needs to be the first exam in the test list UI
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

    def test_guest_cannot_access_exam_pages(self):
        self.logout()
        # try to access an exam page as guest
        self.get_page_redirects_to_login_url(self.exam_page_url)
        # try to access the test list page as guest
        self.get_page_redirects_to_login_url(self.test_list_url)