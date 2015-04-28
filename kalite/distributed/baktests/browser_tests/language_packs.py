"""
These use a web-browser, along selenium, to simulate user actions.
"""
import mock
import os
import time
import urllib
from selenium.webdriver.common.keys import Keys

from django.conf import settings
from django.core.management import call_command
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.i18n import get_installed_language_packs

logging = settings.LOG


@unittest.skipIf(getattr(settings, 'HEADLESS', None), "Doesn't work on HEADLESS.")
class LanguagePackTest(CreateAdminMixin, BrowserActionMixins, KALiteBrowserTestCase):

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        super(LanguagePackTest, self).setUp()

    def is_language_installed(self, lang_code, force_reload=True):
        return lang_code in get_installed_language_packs(force=force_reload)

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Skip tests that fail when run on Travis, but succeed locally.")
    @mock.patch.object(urllib, 'urlretrieve')
    def test_delete_language_pack(self, urlretrieve_method):
        ''' Test to check whether a language pack is deleted successfully or not '''
        test_zip_filepath = os.path.join(os.path.dirname(__file__), 'de.zip')
        urlretrieve_method.return_value = [test_zip_filepath, open(test_zip_filepath)]
        # Login as admin
        self.browser_login_admin(**self.admin_data)

        # Delete the language pack
        if not self.is_language_installed("de"):
            call_command("languagepackdownload", lang_code="de")

        self.register_device()
        language_url = self.reverse("update_languages")
        self.browse_to(language_url)
        time.sleep(1)
        self.browser.find_element_by_css_selector(".delete-language-button > button[value='de']").click()
        time.sleep(0.5)
        self.browser_send_keys(Keys.RETURN)
        time.sleep(1)
        self.assertFalse(self.is_language_installed("de"))
