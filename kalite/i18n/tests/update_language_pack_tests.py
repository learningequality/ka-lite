import requests
from mock import Mock, patch

from django.core.management.base import CommandError
from django.conf import settings
from django.utils import unittest

import i18n.management.commands.update_language_packs as ulp


class DownloadLatestTranslationTests(unittest.TestCase):
    def test_success(self):
        self.assertTrue(True)

    def setUp(self):
        self.download_translation_args = {'project_id': 'doesntmatter',
                                          'project_key': 'doesntmatter'}

    def test_return_none_if_no_crowdin_credentials(self):
        with patch('settings.CROWDIN_PROJECT_ID', return_value=None, create=True):
            with patch('settings.CROWDIN_PROJECT_KEY', return_value=None, create=True):
                self.assertIsNone(ulp.download_latest_translations())

    @patch.object(requests, 'get', Mock(requests.models.Response))
    def test_error_if_401_unauthorized(self):
        requests.get.return_value.raise_for_status.side_effect = Exception
        requests.get.return_value.status_code = 401
        self.assertRaisesRegexp(CommandError, '401 Unauthorized', lambda: ulp.download_latest_translations(**self.download_translation_args))
