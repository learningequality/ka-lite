import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test import Client, TestCase
from django.utils import unittest

from selenium.common.exceptions import NoSuchElementException
from tastypie.test import ResourceTestCase

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase, \
    KALiteDistributedWithFacilityBrowserTestCase
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.testing.client import KALiteClient
from kalite.testing.mixins.facility_mixins import CreateStudentMixin, CreateTeacherMixin, CreateFacilityMixin

from .utils import get_exam_mode_on, set_exam_mode_on

logging = settings.LOG


class BaseTest(CreateStudentMixin, CreateTeacherMixin, CreateFacilityMixin, ResourceTestCase):

    student_username = 'student'
    student_password = 'password'
    teacher_username = 'teacher'
    teacher_password = 'password'
    facility_name = 'facility'
    facility = None
    teacher = None
    student = None
    exam_id = '128'
    login_url = reverse('login')
    test_list_url = reverse('test_list')
    exam_page_url = reverse('test', args=[exam_id])
    put_url = '/test/api/test/%s/' % exam_id

    def setUp(self):
        super(BaseTest, self).setUp()

        self.max_wait_time = 1
        self.facility = self.create_facility(name=self.facility_name)
        self.assertTrue(self.facility)

        self.teacher = self.create_teacher(username=self.teacher_username,
                                           password=self.teacher_password,
                                           facility=self.facility)
        self.assertTrue(self.teacher)

        self.student = self.create_student(username=self.student_username,
                                           password=self.student_password,
                                           facility=self.facility)
        self.assertTrue(self.student)


class CoreTests(BaseTest):

    def setUp(self):
        super(CoreTests, self).setUp()

    def tearDown(self):
        super(CoreTests, self).tearDown()

    # TODO(cpauya): some methods for Tastypie tests
    # def get_credentials(self, username, password):
    #     return self.create_basic(username=username, password=password)
    #
    # def teacher_auth(self):
    #     return self.get_credentials(self.teacher_username, self.teacher_password)
    #
    # def student_auth(self):
    #     return self.get_credentials(self.student_username, self.student_password)

    def login_teacher(self, client=None):
        data = {
            'username': self.teacher_username,
            'password': self.teacher_password,
            'facility': self.facility.id
        }
        if not client:
            client = self.client
        response = client.post(self.login_url, data=data, follow=True)
        url = reverse('coach_reports')
        self.assertEqual(response.request['PATH_INFO'], url)
        # check content for teacher
        text = "Coach Reports"
        self.assertContains(response, text)
        # browse to the test list page to populate the test cache
        response_tests = client.get(self.test_list_url, follow=True)
        self.assertEqual(response_tests.request['PATH_INFO'], self.test_list_url)
        return response

    def login_student(self, url='/'):
        data = {
            'username': self.student_username,
            'password': self.student_password,
            'facility': self.facility.id
        }
        response = self.client.post(self.login_url, data=data, follow=True)
        self.assertEqual(response.request['PATH_INFO'], url)
        if url == '/':
            text = "Assigned Playlists"
            self.assertContains(response, text)
        if url == self.exam_page_url:
            text = '<title>Take Test | KA Lite</title>'
            self.assertContains(response, text)
        return response

    def test_teacher_can_access_test_list_page(self):
        response = self.login_teacher()
        # try to browse the test list page as teacher
        response = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.test_list_url)

    def test_student_cannot_access_test_list_page(self):
        # make sure we don't have exam mode on
        set_exam_mode_on('')
        response = self.login_student()
        # any attempt to browse the test list page as student will redirect to login page
        response = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.login_url)

    def test_student_cannot_access_exam_page_if_not_exam_mode(self):
        # make sure we don't have exam mode on
        set_exam_mode_on('')
        response = self.login_student()
        # any attempt to browse the exam page as student will raise a 404
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_teacher_toggle_exam_mode(self):
        data = {}
        set_exam_mode_on('')  # set exam mode
        response = self.login_teacher()
        response = self.client.get(self.put_url)  # this will fill the testcache
        response = self.client.put(self.put_url, data=data, content_type='application/json')  # set exam mode
        # check student access on exam mode
        response = self.login_student(url=self.exam_page_url)
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.exam_page_url)

        # reset exam mode
        response = self.login_teacher()
        response = self.client.get(self.put_url)  # this will fill the testcache
        response = self.client.put(self.put_url, data=data, content_type='application/json')
        # check student access if not on exam mode
        response = self.login_student()
        # any attempt to browse the exam page as student will raise a 404
        response = self.client.get(self.exam_page_url, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_redirect_student_if_exam_mode(self):
        """
        Login as teacher, set exam mode, then check the student if student is redirected to the exam page.

        option 1. set exam mode by code
        option 2. set exam mode by client.put call
        option 3. set exam mode by tastypie api
        """

        def _check_student_access_to_exam(url=None):
            if not url:
                url = reverse('test', args=[self.exam_id])
            self.assertEqual(get_exam_mode_on(), self.exam_id)

            # logged-in student must be redirected to the exam page
            response = self.login_student(url)
            text = 'test_id: "%s"' % self.exam_id
            self.assertContains(response, text)
            self.assertEqual(response.request['PATH_INFO'], url)

        # TODO(cpauya): option 1. set exam mode by code
        response = self.login_teacher()
        set_exam_mode_on(self.exam_id)
        _check_student_access_to_exam()

        # TODO(cpauya): option 2. set exam mode by client.put call
        data = {}
        set_exam_mode_on('')  # reset exam mode
        response = self.login_teacher()
        response = self.client.get(self.put_url)  # this will fill the testcache
        response = self.client.put(self.put_url, data=data, content_type='application/json')  # set exam mode
        _check_student_access_to_exam()

        # TODO(cpauya): option 3. set exam mode by tastypie api
        # from tastypie.test import TestApiClient
        # client = TestApiClient()

        # set_exam_mode_on('')  # reset exam mode
        # response = self.login_teacher()
        # data = {
        # }
        # # data = self.teacher_auth()
        # response = self.client.get(self.put_url, data=data, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # # # logging.warn('==> response %s' % response)
        # # text = '"test_id": "128"'
        # # self.assertContains(response, text)
        # self.assertEqual(response.request['PATH_INFO'], self.put_url)
        # _check_student_access_to_exam()


# # TODO(cpauya): browser tests for exam mode
# class BrowserTests(BaseTest, KALiteDistributedWithFacilityBrowserTestCase):
#
#     def setUp(self):
#         # super(KALiteDistributedBrowserTestCase, self).setUp()
#         super(BrowserTests, self).setUp()
#
#     def tearDown(self):
#         super(BrowserTests, self).tearDown()
#
#     def test_teacher_enable_exam_mode(self):
#         self.browser_login_teacher(username=self.teacher_username,
#                                    password=self.teacher_password,
#                                    facility_name=self.facility.name)
#         self.browse_to(self.test_list_url)
#         # with self.assertRaises(NoSuchElementException):
#         # self.browser.find_element_by_css_selector('.test-row-button')


# TODO(cpauya): references for possible unit tests
# class StudentTestingTests(CreateCoachMixin, CreateStudentMixin, TestCase):
#
#     def setUp(self):
#         self.create_student()
#         self.create_coach()
#         self.client = Client()
#         self.test_list_url = reverse('test_list')
#
#     def test_coach_can_access_test_list_page(self):
#         self.coach_username = CreateCoachMixin.DEFAULTS['username']
#         self.coach_password = CreateCoachMixin.DEFAULTS['password']
#         result = self.client.login(username=self.coach_username, password=self.coach_password)
#         self.assertTrue(result)
#         self.assertFalse(True)
#
#     def test_coach_can_access_test_page(self):
#         self.assertFalse(True)
#
#     def test_admin_can_access_test_page(self):
#         self.assertFalse(True)
#
#     def test_admin_can_access_test_list_page(self):
#         self.assertFalse(True)
#
#     def test_student_cannot_access_test_list_page(self):
#         self.assertFalse(True)
#
#     def test_student_cannot_access_test_page_if_no_exam(self):
#         self.assertFalse(True)
#
#     def test_redirect_student_to_exam_page(self):
#         self.assertFalse(True)
#
#     def test_guest_can_access_test_page_on_exam_mode(self):
#         self.assertFalse(True)
#
#     def test_guest_cannot_access_test_page(self):
#         self.assertFalse(True)
#
#     def test_guest_cannot_access_test_list_page(self):
#         self.assertFalse(True)
#
#
# class StudentTestingAPITests(CreateCoachMixin, CreateStudentMixin, TestCase):
#
#     def setUp(self):
#         self.create_student()
#         self.create_coach()
#
#     def test_list_page_url_exists(self):
#         self.assertFalse(True)
#
#     def test_student_cannot_access_test_list_page(self):
#         self.assertFalse(True)
