"""
"""
import os
import random
import re

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import unittest

import settings
from .base import MainTestCase
from facility.models import Facility, FacilityUser
from testing.client import KALiteClient
from testing.decorators import distributed_server_test
from utils.django_utils import call_command_with_output


@distributed_server_test
class ChangeLocalUserPassword(MainTestCase):
    """Tests for the changelocalpassword command"""

    def setUp(self):
        """Create a new facility and facility user"""
        super(ChangeLocalUserPassword, self).setUp()

        self.old_password = 'testpass'
        self.username = "testuser"
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.username, facility=self.facility)
        self.user.set_password(self.old_password)
        self.user.save()


    def test_change_password_on_existing_user(self):
        """Change the password on an existing user."""

        # Now, re-retrieve the user, to check.
        (out,err,val) = call_command_with_output("changelocalpassword", self.user.username, noinput=True)
        self.assertEqual(err, "", "no output on stderr")
        self.assertNotEqual(out, "", "some output on stdout")
        self.assertEqual(val, 0, "Exit code is not zero")

        new_password =  re.search(r"Generated new password for user .*: '(?P<password>.*)'", out).group('password')
        self.assertNotEqual(self.old_password, new_password)

        c = KALiteClient()
        success = c.login(username=self.user.username, password=new_password, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")


    def test_change_password_on_nonexistent_user(self):
        nonexistent_username = "voiduser"
        with self.assertRaises(CommandError):
            (out, err, val) = call_command_with_output("changelocalpassword", nonexistent_username, noinput=True)
