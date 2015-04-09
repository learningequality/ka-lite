"""
Base classes to help test i18n functions
"""
import logging
import os
import urllib
from mock import patch

from django.core.management import call_command
from django.test import TestCase

from .. import get_installed_language_packs, delete_language


class I18nTestCase(TestCase):

    def is_language_installed(self, lang_code, force_reload=True):
        return lang_code in get_installed_language_packs(force=force_reload)

    @patch.object(urllib, 'urlretrieve')
    def install_language(self, lang_code, urlretrieve_method):
        test_zip_filepath = os.path.join(os.path.dirname(__file__), 'testzips', '%s.zip' % lang_code)
        urlretrieve_method.return_value = [test_zip_filepath, open(test_zip_filepath)]

        if not self.is_language_installed(lang_code):
            call_command('languagepackdownload', lang_code=lang_code)

    def install_languages(self):
        # install TEST_LANGUAGES, if defined
        if not self.TEST_LANGUAGES:
            logging.debug("self.TEST_LANGUAGES not defined. Not installing any language.")
        else:
            logging.disable(logging.ERROR) # silence langpack installation logs

            for lang in self.TEST_LANGUAGES:
                self.install_language(lang)

            logging.disable(logging.NOTSET) # reactivate logs again


    def uninstall_languages(self):
        logging.disable(logging.ERROR)

        for lang in self.TEST_LANGUAGES:
            delete_language(lang)

        logging.disable(logging.NOTSET)
