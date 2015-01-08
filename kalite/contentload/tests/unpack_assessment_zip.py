import os
import requests
import zipfile
from mock import patch, MagicMock, mock_open

from django.conf import settings
from django.core.management import call_command

from kalite.testing import KALiteTestCase
from kalite.contentload.management.commands import unpack_assessment_zip as mod


class UnpackAssessmentZipCommandTests(KALiteTestCase):

    @patch.object(mod, "unpack_zipfile_to_khan_content")
    @patch.object(requests, "get")
    def test_fetches_zip_if_given_url(self, get_method, unpack_method):
        get_method.return_value = MagicMock(content="string")

        url = "http://some-valid-url.com/test.zip"

        call_command("unpack_assessment_zip", url)

        get_method.assert_called_once_with(url)
        self.assertEqual(unpack_method.call_count, 1)

    @patch("%s.open" % __name__, mock_open, create=True)
    def test_opens_file_if_invalid_url(self):
        loc = "/somewhere/test.zip"

        call_command("unpack_assessment_zip", loc)

        mock_open.assert_called_once_with(loc, "r")


class UnpackAssessmentZipUtilityFunctionTests(KALiteTestCase):

    def test_unpack_zipfile_to_khan_content_extracts_to_content_dir(self):
        zipfile_instance = MagicMock()

        extract_dir = settings.ASSESSMENT_ITEMS_RESOURCES_DIR

        mod.unpack_zipfile_to_khan_content(zipfile_instance)

        zipfile_instance.extractall.assert_called_once_with(extract_dir)


    def test_is_valid_url_returns_false_for_invalid_urls(self):
        invalid_urls = [
            "/something.path",
            "/path/to/somewhere"
            ]

        for url in invalid_urls:
            self.assertFalse(mod.is_valid_url(url))


    def test_is_valid_url_returns_true_for_valid_urls(self):
        pass

        valid_urls = [
            "http://stackoverflow.com/questions/25259134/how-can-i-check-whether-a-url-is-valid-using-urlparse",
            "http://en.wikipedia.org/wiki/Internationalized_resource_identifier"
        ]

        for url in valid_urls:
            self.assertTrue(mod.is_valid_url(url))
