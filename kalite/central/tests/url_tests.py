"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os

from django.test import LiveServerTestCase, TestCase, Client
from django.core.management import call_command

import settings
from testing import central_server_test


@central_server_test
class UrlTestCases(LiveServerTestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def validate_url(self, url, status_code=200, find_str=None):
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code)" % url)
        if find_str is not None:
            self.assertTrue(find_str in resp.content, "%s (check content)" % url)


    def test_urls(self):
        self.validate_url('/')
        self.validate_url('/accounts/login/')
        self.validate_url('/accounts/register/')

