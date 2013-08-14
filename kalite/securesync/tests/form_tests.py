from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from securesync.forms import FacilityUserForm
from securesync.models import Facility, FacilityUser

class UserRegistration(TestCase):

    def setUp(self):
        self.f = Facility.objects.create(name='testfac')
        password = make_password('insecure')
        self.admin = User.objects.create(username='testadmin',
                                              password=password)
        self.data = {'username': 'testuser',
                'facility': self.f.id,
                'password': 'doesntmatter',
                'password_recheck': 'doesntmatter',
        }

    def test_facility_user_form_works(self):
        response = self.client.post(reverse('add_facility_student'), self.data)
        FacilityUser.objects.get(username=self.data['username']) # should not raise error

    def test_admin_and_user_no_common_username(self):
        self.data['username'] = self.admin.username
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertFormError(response, 'form', 'username', 'The specified username is unavailable. Please choose a new username and try again.')
