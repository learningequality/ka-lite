"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import unittest
#from selenium 
from django.test import TestCase, Client
from django.core.management import call_command

import settings


class UrlTestCases(TestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def setUp(self):
        cur_dir = os.path.split(__file__)[0]
        fixture_file = cur_dir + "/central_fixture.json"
        call_command("loaddata", fixture_file)

    def validate_url(self, url, status_code=200, find_str=None):
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code)" % url)
        if find_str is not None:
            self.assertNotEqual(-1, resp.content.find(find_str), "%s (check content)" % url)
        
        
    def test_urls(self):
#        import pdb; pdb.set_trace()
        self.validate_url('/')
        self.validate_url('/accounts/login/')
        self.validate_url('/accounts/register/')
        
        
        
        