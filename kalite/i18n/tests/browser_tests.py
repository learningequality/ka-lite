# encoding: UTF-8
from django.conf import settings
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
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
