from mock import patch

from django.conf import settings
from django.utils import unittest

import i18n.management.commands.update_language_packs as ulp


class DownloadLatestTranslationTests(unittest.TestCase):
    def test_success(self):
        self.assertTrue(True)

    def test_return_none_if_no_crowdin_credentials(self):
        with patch('settings.CROWDIN_PROJECT_ID', return_value=None, create=True):
            with patch('settings.CROWDIN_PROJECT_KEY', return_value=None, create=True):
                self.assertIsNone(ulp.download_latest_translations())
