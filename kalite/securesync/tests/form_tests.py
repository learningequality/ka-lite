from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase

from securesync.forms import FacilityUserForm
from securesync.models import Facility

class UserRegistration(TestCase):

    def setUp(self):
        self.f = Facility.objects.create(name='testfac')
        password = make_password('insecure')
        self.admin = User.objects.create(username='testadmin',
                                              password=password)

    def test_admin_and_user_no_common_username(self):
        data = {'username': self.admin.username,
                'facility': self.f,
                'group': None,
                'password': 'doesntmatter',
                'password_recheck': 'doesntmatter',
        }
        response = self.client.post('/securesync/addstudent/', data)
        self.assertFormError(response, 'form', 'username', 'An administrator with this username exists. Please choose a new username and try again.')
