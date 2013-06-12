"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import unittest

from django.test import TestCase
from django.core.management import call_command

import settings


class FixtureTestCases(TestCase):
    """ """

    def test_loaddata(self):
        cur_dir = os.path.split(__file__)[0]
        
        fixture_file = cur_dir + "/main_fixture.json"
        out = call_command("loaddata", fixture_file, "Just make sure that loaddata doesn't throw an error, for now")


    def test_dumpdata(self):
        out = call_command("dumpdata", "main")
        self.assertEqual(out, None, "Just make sure that dumpdata doesn't throw an error, for now")