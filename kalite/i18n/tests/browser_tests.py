# encoding: UTF-8
import time

from django.conf import settings
from django.utils import unittest

from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.i18n.tests.base import I18nTestCase


class BrowserLanguageSwitchingTests(KALiteDistributedBrowserTestCase, I18nTestCase):

    TEST_LANGUAGES = ['it', 'pt-BR']

    def setUp(self):
        self.foreign_language_homepage_text_mappings = {
            'it': "gratuita per chiunque ovunque",
            'pt-BR': "Uma educação sem salas de aula para qualquer um em qualquer lugar",
        }
        assert sorted(self.TEST_LANGUAGES) == sorted(self.foreign_language_homepage_text_mappings.keys())

        super(KALiteDistributedBrowserTestCase, self).setUp()
        self.install_languages()

    def tearDown(self):
        self.uninstall_languages()
        super(KALiteDistributedBrowserTestCase, self).tearDown()

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Fails on tests, but works in actual usage")
    def test_logged_out_homepage_language_switches_from_english_and_back(self):
        english_text = "A free world-class education for anyone anywhere"

        for lang_code, expected_text in self.foreign_language_homepage_text_mappings.iteritems():
            self.browse_to(self.reverse("homepage"))
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % lang_code).click()
            time.sleep(1)
            self.browse_to(self.reverse("homepage"))
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)

            # switch back to english, and test that we successfully switched back
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % "en").click()
            time.sleep(1)
            self.browse_to(self.reverse("homepage"))
            self.assertIn(english_text, self.browser.find_element_by_css_selector(".main-headline").text)

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Fails on tests, but works in actual usage")
    def test_set_server_default_language(self):
        self.browser_login_admin()
        self.register_device()

        for lang, expected_text in self.foreign_language_homepage_text_mappings.iteritems():
            self.browse_to(self.reverse("update_languages"))
            self.browser.find_element_by_css_selector(".set_server_language[value='%s']" % lang).click()

            self.browse_to(self.reverse("homepage"))
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)
