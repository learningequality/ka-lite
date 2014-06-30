
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import unittest

from .base import I18nTestCase


@unittest.skipIf(settings.RUNNING_IN_TRAVIS, 'Passes locally but fails on travis somehow')
class JSCatalogTests(I18nTestCase):

    TEST_LANGUAGES = ['de', 'it', 'pt-BR']

    def setUp(self):
        self.install_languages()

    def tearDown(self):
        self.uninstall_languages()

    def test_catalog_files_are_present(self):
        for lang in self.TEST_LANGUAGES:
            path = finders.find("js/i18n/%s.js" % lang)
            self.assertIsNotNone(path)
