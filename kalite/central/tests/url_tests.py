"""
Tests across various URLs of the central app
"""

import os

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase, Client


class UrlTestCases(TestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def setUp(self):
        """Load a fixture of data, for easy setup"""
        cur_dir = os.path.split(__file__)[0]
        fixture_file = cur_dir + "/central_fixture.json"
        call_command("loaddata", fixture_file)

    def validate_url(self, url, status_code=200, find_str=None):
        """GET a url, validate that the status code is correct, optionally validate a string"""
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code)" % url)
        if find_str is not None:
            self.assertTrue(find_str in resp.content, "%s (check content)" % url)
        
    def test_urls(self):
        """Test some basic URLs on the project (will detect 500 errors, for example)"""
        self.validate_url(reverse('homepage'))
        self.validate_url(reverse('auth_login'))
        self.validate_url(reverse('registration_register'))
        
        
        
        