"""
Base classes to help test i18n functions
"""
from django.core.management import call_command
from django.test import Client, TestCase

from .. import get_installed_language_packs


class I18nTestCase(TestCase):

    # TODO (ARON): move useful utility to either a module or TestCase subclass
    def is_language_installed(self, lang_code, force_reload=True):
        return lang_code in get_installed_language_packs(force=force_reload)

    def install_language(self, lang_code):
        if not self.is_language_installed(lang_code):
            call_command('languagepackdownload', lang_code=lang_code)

    def setUp(self):
        self.client = Client()
        super(TestCase, self).setUp()
