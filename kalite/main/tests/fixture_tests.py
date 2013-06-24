"""

"""

import os

from django.test import TestCase
from django.core.management import call_command
from django.db import DatabaseError

from kalite import settings
from utils.testing.decorators import distributed_only


@distributed_only
class FixtureTestCases(TestCase):
    """ """

    def test_loaddata(self):
        cur_dir = os.path.split(__file__)[0]
        
        fixture_file = cur_dir + "/main_fixture.json"
        out = call_command("loaddata", fixture_file, "Just make sure that loaddata doesn't throw an error, for now")


    def test_dumpdata(self):
        
        # 
        self.assertEqual(call_command("dumpdata", "main"), None, "call_command always returns none.  We're just making sure it doesn't raise an Exception")
        
        # Kill the data
        # Dumpdata should fail when we've taken down the main app"
        call_command("migrate", "main", "zero")
        with self.assertRaises(DatabaseError):
            call_command("dumpdata", "main")
        call_command("migrate", "main")