import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test import Client, TestCase
from django.utils import unittest

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
# from kalite.distributed.tests.browser_tests.base import KALiteDistributedWithFacilityBrowserTestCase
from kalite.testing.mixins.facility_mixins import CreateStudentMixin, CreateTeacherMixin, CreateFacilityMixin

logging = settings.LOG


class BrowserTests(CreateStudentMixin, CreateTeacherMixin, CreateFacilityMixin, TestCase):
# class BrowserTests(CreateStudentMixin, CreateTeacherMixin, CreateFacilityMixin,
#                    KALiteDistributedBrowserTestCase):
# class BrowserTests(CreateStudentMixin, CreateTeacherMixin, KALiteDistributedWithFacilityBrowserTestCase):

    student_username = 'student1'
    student_password = 'password'

    teacher_username = 'teacher1'
    teacher_password = 'password'

    facility_name = 'facility'
    facility = None
    teacher = None
    student = None

    exam_id = '128'

    def setUp(self):
        super(BrowserTests, self).setUp()

        self.max_wait_time = 1
        self.facility = self.create_facility(name=self.facility_name)

        self.teacher = self.create_teacher(username=self.teacher_username,
                                           password=self.teacher_password,
                                           facility=self.facility)

        self.assertTrue(self.teacher)

        self.student = self.create_student(username=self.student_username,
                                           password=self.student_password,
                                           facility=self.facility)
        self.assertTrue(self.student)

        self.login_url = reverse('login')
        self.test_list_url = reverse('test_list')

    def tearDown(self):
        super(BrowserTests, self).tearDown()

    def http_auth(self, username, password):
        import base64
        credentials = base64.encodestring('%s:%s' % (username, password)).strip()
        auth_string = 'Basic %s' % credentials
        return auth_string

    def login_teacher(self):
        data = {
            'username': self.teacher_username,
            'password': self.teacher_password,
            'facility': self.facility.id
        }
        return self.client.post(self.login_url, data=data, follow=True)

    def teacher_auth(self):
        return {
            'HTTP_AUTHORIZATION': self.http_auth(self.teacher_username,
                                                 self.teacher_password)
        }

    def login_student(self):
        data = {
            'username': self.student_username,
            'password': self.student_password,
            'facility': self.facility.id
        }
        return self.client.post(self.login_url, data=data, follow=True)

    def student_auth(self):
        return {
            'HTTP_AUTHORIZATION': self.http_auth(self.student_username,
                                                 self.student_password)
        }

    def test_teacher_can_access_test_list_page(self):
        response = self.login_teacher()
        url = reverse('coach_reports')
        self.assertEqual(response.request['PATH_INFO'], url)
        # check content
        text = "Coach Reports"
        self.assertContains(response, text)
        # try to browse the test list page as teacher
        response = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.test_list_url)

    def test_student_cannot_access_test_list_page(self):
        response = self.login_student()
        self.assertEqual(response.request['PATH_INFO'], '/')
        # check content
        text = "Assigned Playlists"
        self.assertContains(response, text)
        # try to browse the test list page as student
        response = self.client.get(self.test_list_url, follow=True)
        # did student redirect to login page?
        self.assertEqual(response.request['PATH_INFO'], self.login_url)

    def test_teacher_enable_exam_mode(self):
        self.login_teacher()
        self.fail('TODO')

    def test_teacher_disable_exam_mode(self):
        self.login_teacher()
        self.fail('TODO')

    def test_redirect_student_if_exam_mode(self):
        """
        option 1. set exam mode by tastypie api
        option 2. set exam mode by post/browser call
        option 3. set exam mode by code
        """

        response = self.login_teacher()
        # logging.warn('==> response %s' % response)

        # TODO(cpauya): option 1. set exam mode by tastypie api
        # from tastypie.test import TestApiClient
        # client = TestApiClient()
        # url = '/test/api/test/'
        # data = {
        #     'exam_id': self.exam_id
        # }
        # url = '/test/api/test/128/'
        # data = {}
        # extra = self.teacher_auth()
        # response = client.put(url, data=data, **extra)
        # # logging.warn('==> response %s' % response)

        # TODO(cpauya): option 2. set exam mode by post/browser call
        # url = '/test/api/test/%s/' % self.exam_id
        # data = {
        # }
        # response = self.client.post(url, data=data, follow=True)
        # # logging.warn('==> response %s' % response)
        # text = '"test_id": "128"'
        # self.assertContains(response, text)
        # self.assertEqual(response.request['PATH_INFO'], url)

        # TODO(cpauya): option 3. set exam mode by code
        from student_testing.utils import set_exam_mode_on
        set_exam_mode_on(self.exam_id)

        from student_testing.utils import get_exam_mode_on
        self.assertEqual(get_exam_mode_on(), self.exam_id)

        # logged-in student must be redirected to the exam page
        response = self.login_student()
        # logging.warn('==> response %s' % response)
        text = 'test_id: "128"'
        self.assertContains(response, text)
        url = reverse('test', args=[self.exam_id])
        self.assertEqual(response.request['PATH_INFO'], url)


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
