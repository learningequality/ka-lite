import StringIO
import os
import shutil
import tempfile
import zipfile

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

    @patch.object(settings, 'CROWDIN_PROJECT_ID', None, create=True)
    @patch.object(settings, 'CROWDIN_PROJECT_KEY', None, create=True)
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

    # mock requests.get to return the zip, check that it's extracted to where mkdtemp tells it to (which we also mock)
    @patch.object(tempfile, 'mkdtemp')
    @patch.object(requests, 'get')
    def test_success_zip_extracted(self, get_method, mkdtemp_method):
        test_zip_path = os.path.join(os.path.dirname(__file__), 'test.zip')
        test_zip_contents = ['working.txt']
        extract_path = os.path.join(os.path.dirname(__file__), 'tmp')

        if os.path.exists(extract_path):
            shutil.rmtree(extract_path) # clear the test extract path first

        with open(test_zip_path) as f:
            fcontents = f.read()
            mkdtemp_method.return_value = extract_path
            get_method.return_value = Mock(Response, status_code=200, content=fcontents)

        # we dont want to build the po files in the zip, so stub it
        with patch.object(ulp, 'build_new_po'):
            # we dont want it to delete the extracted path too, so dont delete it
            with patch.object(shutil, 'rmtree'):
                ulp.download_latest_translations(**self.download_translation_args)

        for test_content in test_zip_contents:
            test_path = os.path.join(extract_path, test_content)
            self.assertTrue(os.path.exists(test_path))
