"""
Tests of the organization invitation system
"""
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import LiveServerTestCase, TestCase, Client

import settings
from central.models import Organization, OrganizationInvitation
from testing import central_server_test


@central_server_test
class InvitationTestCases(LiveServerTestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def setUp(self):
        self.user, _ = User.objects.get_or_create(username="u1")
        self.non_user, _ = User.objects.get_or_create(username="u2")
        self.organization, _ = Organization.objects.get_or_create(name="ben", owner=self.user)
        self.organization.users.add(self.user)

    def test_good_invitation(self):
        OrganizationInvitation(organization = self.organization, invited_by=self.user).save()

    def test_bad_invitation(self):
        with self.assertRaises(PermissionDenied):
            OrganizationInvitation(organization = self.organization, invited_by=self.non_user).save()
