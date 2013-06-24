"""
Tests for exploring URLs within the "main" app
"""

import os

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

import settings
from utils.testing.decorators import distributed_only


@distributed_only
class UrlTestCases(TestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def setUp(self):
        """Load a fixture, for easy data setup."""
        cur_dir = os.path.split(__file__)[0]
        fixture_file = cur_dir + "/main_fixture.json"
        call_command("loaddata", fixture_file)

    def validate_url(self, url, status_code=200, find_str=None):
        """Validate a URL via status code response, and an optional search string."""
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code=%d != %d)" % (url, status_code, resp.status_code))
        if find_str is not None:
            self.assertIn(find_str, resp.content, "%s (check content)" % url)
        
        
    def test_urls(self):
        settings.DEBUG=False
        self.validate_url(reverse("homepage"))
        self.validate_url(reverse("exercise_dashboard"))
        self.validate_url(reverse("login"))
        self.validate_url(reverse("add_facility_student"), status_code=302)

        self.validate_url('/math/') # topic tree
        self.validate_url('/topics/', status_code=404) # old topic tree
        self.validate_url('/content/', status_code=404) # nothing

        # Central server URLs
        self.validate_url('/accounts/login/', status_code=404)
        self.validate_url('/accounts/register/', status_code=404)

        
        