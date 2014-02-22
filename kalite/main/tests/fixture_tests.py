"""

"""
import os

from django.core.management import call_command
from django.db import DatabaseError
from django.utils import unittest

import settings
from testing import distributed_server_test, KALiteTestCase


@distributed_server_test
class FixtureTestCases(KALiteTestCase):
    """ """

    def test_loaddata(self):
        cur_dir = os.path.split(__file__)[0]

        fixture_file = cur_dir + "/main_fixture.json"
        out = call_command("loaddata", fixture_file, "Just make sure that loaddata doesn't throw an error, for now")

    def test_dumpdata(self):

        #
        self.assertEqual(call_command("dumpdata", "main"), None, "call_command always returns none.  We're just making sure it doesn't raise an Exception")
        #call_command("migrate", "main", "zero")
        call_command("dumpdata", "main")
        #call_command("migrate", "main")
