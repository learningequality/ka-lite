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

    def is_language_installed(self,lang_code):
        flag = False	# flag to check language de is installed or not
        installed_languages= get_installed_language_packs()
        for lang in installed_languages:
            if lang == lang_code:
                flag = True
                break
        return flag

    # def test_add_language_pack(self):
    #     # Login as admin
    #     self.browser_login_admin()

    #     # Add the language pack
    #     if self.is_language_installed("de"):
    #         # what we want to test is if adding a language pack works.
    #         # So we uninstall "de" to be able to test it
    #         delete_language("de")

    #     self.register_device()
    #     language_url = self.reverse("update_languages")
    #     self.browse_to(language_url)
    #     time.sleep(3)
    #     select = self.browser.find_element_by_id("language-packs")
    #     for option in select.find_elements_by_tag_name('option'):
    #         if option.text == "German (de)":
    #             option.click()
    #     time.sleep(1)
    #     self.browser.find_element_by_css_selector("#get-language-button").click()
    #     time.sleep(5)

    #     self.assertTrue(self.is_language_installed("de"))

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

        self.assertFalse(self.is_language_installed("de"))
