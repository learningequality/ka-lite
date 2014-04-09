"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.webdriver.firefox.webdriver import WebDriver

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from django.utils.translation import ugettext as _

from .base import KALiteDistributedBrowserTestCase
from kalite.i18n import get_installed_language_packs
from kalite.main.models import ExerciseLog
from kalite.updates import delete_language


class LanguagePackTest(KALiteDistributedBrowserTestCase):

    def is_language_installed(self, lang_code, force_reload=True):
        return lang_code in get_installed_language_packs(force=force_reload)

    def test_delete_language_pack(self):
        ''' Test to check whether a language pack is deleted successfully or not '''
        # Login as admin
        self.browser_login_admin()

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
