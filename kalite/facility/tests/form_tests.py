"""
"""
import string

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..forms import FacilityUserForm
from ..models import Facility, FacilityUser
from kalite.testing import KALiteTestCase


class UserRegistrationTest(KALiteTestCase):

    def setUp(self):
        super(UserRegistrationTest, self).setUp()
        self.f = Facility.objects.create(name='testfac')
        password = make_password('insecure')
        self.admin = User.objects.create(username='testadmin',password=password)
        self.data = {
            'username': 'testuser',
            'facility': self.f.id,
            'default_language': 'en',
        }
        self.data['password_first'] = self.data['password_recheck'] = 'k' * settings.PASSWORD_CONSTRAINTS['min_length']

    def test_facility_user_form_works(self):
        """Valid password should work"""
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error

    def test_admin_and_user_no_common_username(self):
        """Post as username"""
        self.data['username'] = self.admin.username
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'username', 'The specified username is unavailable. Please choose a new username and try again.')

    def test_password_length_valid(self):
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error

    def test_password_length_enforced(self):
        # always make passwd shorter than passwd min length setting
        self.data['password_first'] = self.data['password_recheck'] =  self.data['password_first'][:settings.PASSWORD_CONSTRAINTS['min_length']-1]

        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'password_first', "Password should be at least %d characters." % settings.PASSWORD_CONSTRAINTS['min_length'])

    def test_only_ascii_letters_allowed(self):
        self.data['password_first'] = self.data['password_recheck'] = string.whitespace.join([self.data['password_first']] * 2)

        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error
