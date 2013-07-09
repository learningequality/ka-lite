"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
#from selenium 
from django.test import TestCase, Client
from django.core.management import call_command
from django.utils import unittest

import settings
from utils.testing import distributed_only


@distributed_only
class UrlTestCases(TestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def validate_url(self, url, status_code=200, find_str=None):
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code=%d != %d)" % (url, status_code, resp.status_code))
        if find_str is not None:
            self.assertTrue(find_str in resp.content, "%s (check content)" % url)
        
        
    def test_urls(self):
        settings.DEBUG=False
        self.validate_url('/')
        self.validate_url('/exercisedashboard/')
        self.validate_url('/securesync/login/')
        self.validate_url('/securesync/addstudent/', status_code=302)
        self.validate_url('/math/')
        self.validate_url('/content/', status_code=404)
        self.validate_url('/accounts/login/', status_code=404)
        self.validate_url('/accounts/register/', status_code=404)
        
        
        
        
