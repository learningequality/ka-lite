"""
Contains test wrappers and helper functions for
automated of KA Lite using selenium
for automated browser-based testing.
"""

from selenium import webdriver

from django.core.urlresolvers import reverse
from django.test import TestCase, LiveServerTestCase

from .browser import setup_browser
from .client import KALiteClient
from .mixins import CreateDeviceMixin


class KALiteTestCase(CreateDeviceMixin, TestCase):
    """The base class for KA Lite test cases."""

    def setUp(self):
        self.setup_fake_device()

        super(KALiteTestCase, self).setUp()

    def reverse(self, *args, **kwargs):
        """Regular Django reverse function."""

        return reverse(*args, **kwargs)


class KALiteClientTestCase(KALiteTestCase):

    def setUp(self):
        self.client = KALiteClient()
        self.client.setUp()

        super(KALiteClientTestCase, self).setUp()


class KALiteBrowserTestCase(KALiteTestCase, LiveServerTestCase):

    def setUp(self):
        self.browser = setup_browser(browser_type="Firefox")

        super(KALiteBrowserTestCase, self).setUp()

    def tearDown(self):
        self.browser.quit()

        super(KALiteBrowserTestCase, self).tearDown()

    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(
            url_name,
            args=args,
            kwargs=kwargs,
        )

    @property
    def is_phantomjs(self):
        return isinstance(self.browser, webdriver.PhantomJS)
