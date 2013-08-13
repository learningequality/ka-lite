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
        self.data = {'username': 'testuser',
                'facility': self.f,
                'group': None,
                'password': 'doesntmatter',
                'password_recheck': 'doesntmatter',
        }

    def test_admin_and_user_no_common_username(self):
        response = self.client.post('/securesync/addstudent/', self.data)
        self.assertFormError(response, 'form', 'username', 'The specified username is unavailable. Please choose a new username and try again.')
