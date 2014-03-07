"""
Tests for securesync
"""
from django.test import LiveServerTestCase

from securesync.models import Device


class SecuresyncTestCase(LiveServerTestCase):
    """The base class for KA Lite test cases."""

    def setUp(self):
        Device.own_device = None  # cached within securesync, never cleared out

    def tearDown(self):
        Device.own_device = None  # cached within securesync, never cleared out
