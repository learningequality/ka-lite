"""
Test the basic ability to load and dump data to a fixture.  Very basic.
"""

import os

from django.test import TestCase
from django.core.management import call_command

import settings
from utils.testing import central_only


@central_only
class FixtureTestCases(TestCase):
    """Test the basic ability to load and dump data to a fixture.  Very basic."""

    def test_loaddata(self):
        cur_dir = os.path.split(__file__)[0]
        
        fixture_file = cur_dir + "/central_fixture.json"
        out = call_command("loaddata", fixture_file)


    def test_dumpdata(self):
        out = call_command("dumpdata", "central")
        self.assertEqual(out, None)