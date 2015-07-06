
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from ..models import Facility, FacilityGroup
from kalite.testing.base import KALiteTestCase


class FacilityTestCase(KALiteTestCase):

    def setUp(self):
        super(FacilityTestCase, self).setUp()
        self.facility = Facility.objects.create(name='testfac')
        self.group = FacilityGroup.objects.create(name='testgroup', facility=self.facility)
        self.admin = User.objects.create(username='testadmin', password=make_password('insecure'))
        self.data = {
            'username': u'testuser',
            'first_name': u'fn',
            'facility': self.facility.id,
            'group': self.group.id,
            'is_teacher': False,
            'default_language': 'en',
            'password_first': 'k' * settings.PASSWORD_CONSTRAINTS['min_length'],
            'password_recheck': 'k' * settings.PASSWORD_CONSTRAINTS['min_length'],
        }