import requests
from mock import MagicMock as Mock, patch
from requests.models import Response

from django.core.management.base import CommandError
from django.utils import unittest

import settings
import i18n.management.commands.update_language_packs as ulp


class DownloadLatestTranslationTests(unittest.TestCase):
    def setUp(self):
        self.download_translation_args = {'project_id': 'doesntmatter',
                                          'project_key': 'doesntmatter'}

    @patch.object(settings, 'CROWDIN_PROJECT_ID', None, create=True)
    @patch.object(settings, 'CROWDIN_PROJECT_KEY', None, create=True)
    @patch.object(requests, 'get')
    def test_return_none_if_404(self, get_method):
        get_method.return_value = Mock(Response, status_code=404)
        get_method.return_value.raise_for_status = Mock(side_effect=requests.exceptions.ConnectionError)

        self.assertIsNone(ulp.download_latest_translations())

    @patch.object(requests, 'get')
    def test_error_if_401_unauthorized(self, get_method):
        get_method.return_value = Mock(Response, status_code=401)
        get_method.return_value.raise_for_status = Mock(side_effect=requests.exceptions.ConnectionError)

        self.assertRaisesRegexp(CommandError, '401 Unauthorized', lambda: ulp.download_latest_translations(**self.download_translation_args))

    @patch.object(requests, 'get')
    def test_catchall_error_if_cant_connect(self, get_method):
        get_method.return_value = Mock(Response, status_code=500)
        get_method.return_value.raise_for_status = Mock(side_effect=requests.exceptions.ConnectionError)

        self.assertRaisesRegexp(CommandError, "couldn't connect to CrowdIn API", lambda: ulp.download_latest_translations(**self.download_translation_args))
