"""
"""
from django.conf import settings
from django.utils import unittest

from ..models import FacilityUser


class TestPasswordSetting(unittest.TestCase):

    hashed_blah = "$p5k2$7d0$gTQ4yyg2$cixFA2fd5QUfmKLPWZYIVxoZwymFajCK"

    def test_set_password_hash_ok(self):
        fu = FacilityUser(username="test_user")
        dbg_mode = settings.DEBUG; settings.DEBUG=True
        fu.set_password(hashed_password=self.__class__.hashed_blah)
        settings.DEBUG = dbg_mode
        self.assertTrue(fu.check_password("blah"))

    def test_set_password_raw_ok(self):
        fu = FacilityUser(username="test_user")
        dbg_mode = settings.DEBUG; settings.DEBUG=True
        fu.set_password(raw_password="blahblah")
        settings.DEBUG = dbg_mode
        self.assertTrue(fu.check_password("blahblah"))

    def test_set_password_both_bad(self):
        fu = FacilityUser(username="test_user")
        dbg_mode = settings.DEBUG; settings.DEBUG=True
        with self.assertRaises(AssertionError):
            fu.set_password(raw_password="blue", hashed_password=self.__class__.hashed_blah)
        settings.DEBUG = dbg_mode

    def test_set_password_neither_bad(self):
        fu = FacilityUser(username="test_user")
        dbg_mode = settings.DEBUG; settings.DEBUG=True
        with self.assertRaises(AssertionError):
            fu.set_password()
        settings.DEBUG = dbg_mode

    def test_set_password_hash_nodebug_bad(self):
        fu = FacilityUser(username="test_user")
        dbg_mode = settings.DEBUG; settings.DEBUG=False
        with self.assertRaises(AssertionError):
            fu.set_password(hashed_password=self.__class__.hashed_blah)
        settings.DEBUG = dbg_mode

