import StringIO
import os
import shutil
import tempfile
import zipfile

import requests
from mock import MagicMock as Mock, patch
from requests.models import Response

from django.conf import settings
from django.core.management.base import CommandError
from django.utils import unittest

import i18n.management.commands.update_language_packs as ulp


class DownloadLatestTranslationTests(unittest.TestCase):
    def setUp(self):
        self.extract_path = os.path.join(os.path.dirname(__file__), 'tmp')
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path) # clear the test extract path first

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

    # mock requests.get to return the zip, check that it's extracted to where mkdtemp tells it to (which we also mock)
    @patch.object(shutil, 'rmtree')
    @patch.object(ulp, 'build_new_po')
    @patch.object(tempfile, 'mkdtemp')
    @patch.object(requests, 'get')
    def test_success_zip_extracted_built_and_deleted(self, get_method, mkdtemp_method, build_new_po_method, rmtree_method):
        test_zip_path = os.path.join(os.path.dirname(__file__), 'test.zip')
        test_zip_contents = ['working.txt']

        with open(test_zip_path) as f:
            fcontents = f.read()
            mkdtemp_method.return_value = self.extract_path
            get_method.return_value = Mock(Response, status_code=200, content=fcontents)

        ulp.download_latest_translations(**self.download_translation_args)

        for test_content in test_zip_contents:
            test_path = os.path.join(self.extract_path, test_content)
            self.assertTrue(os.path.exists(test_path))


        assert build_new_po_method.call_count == 1
        rmtree_method.assert_called_once_with(self.extract_path)


class BuildTranslationTests(unittest.TestCase):
    def setUp(self):
        self.download_translation_args = {'project_id': 'doesntmatter',
                                          'project_key': 'doesntmatter'}


    @patch.object(settings.LOG, 'error')
    @patch.object(requests, 'get')
    def test_log_error_if_failed(self, get_method, log_method):
        get_method.return_value = Mock(Response)
        get_method.return_value.raise_for_status.side_effect = requests.exceptions.ConnectionError

        ulp.build_translations(**self.download_translation_args)

        assert log_method.call_count == 1
