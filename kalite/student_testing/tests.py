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

    def test_teacher_can_access_test_list_page(self):
        data = {
            'username': self.teacher_username,
            'password': self.teacher_password,
            'facility': self.facility.id
        }
        # login student
        response = self.client.post(self.login_url, data=data, follow=True)
        url = reverse('coach_reports')
        self.assertEqual(response.request['PATH_INFO'], url)
        # check content
        text = "Coach Reports"
        self.assertContains(response, text)
        # try to browse the test list page as teacher
        response = self.client.get(self.test_list_url, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.test_list_url)

    def test_student_cannot_access_test_list_page(self):
        data = {
            'username': self.student_username,
            'password': self.student_password,
            'facility': self.facility.id
        }
        # login student
        response = self.client.post(self.login_url, data=data, follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/')
        # check content
        text = "Assigned Playlists"
        self.assertContains(response, text)
        # try to browse the test list page as student
        response = self.client.get(self.test_list_url, follow=True)
        # did student redirect to login page?
        self.assertEqual(response.request['PATH_INFO'], self.login_url)


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
