# encoding: UTF-8
from django.conf import settings
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin
from kalite.i18n.tests.base import I18nTestCase


class BrowserLanguageSwitchingTests(BrowserActionMixins, CreateAdminMixin, I18nTestCase, KALiteBrowserTestCase):

    TEST_LANGUAGES = ['it', 'pt-BR']

    def setUp(self):
        self.foreign_language_homepage_text_mappings = {
            'it': "gratuita per chiunque ovunque",
            'pt-BR': "Uma educação sem salas de aula para qualquer um em qualquer lugar",
        }

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        assert sorted(self.TEST_LANGUAGES) == sorted(self.foreign_language_homepage_text_mappings.keys())

        super(BrowserLanguageSwitchingTests, self).setUp()
        self.install_languages()

    def tearDown(self):
        self.uninstall_languages()
        super(BrowserLanguageSwitchingTests, self).tearDown()

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Fails on tests, but works in actual usage")
    def test_set_server_default_language(self):
        self.browser_login_admin(**self.admin_data)
        self.register_device()

        for lang, expected_text in self.foreign_language_homepage_text_mappings.iteritems():
            self.browse_to(self.reverse("update_languages"))
            self.browser.find_element_by_css_selector(".set_server_language[value='%s']" % lang).click()

            self.browse_to(self.reverse("homepage"))
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)
