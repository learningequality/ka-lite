import StringIO
import os
import requests
import zipfile
from mock import patch, MagicMock

from django.conf import settings
from django.core.management import call_command

from kalite.testing import KALiteTestCase
from kalite.contentload.management.commands import unpack_assessment_zip as mod

ASSESSMENT_ZIP_SAMPLE_PATH = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "assessment_item_resources.sample.zip"
)


class UnpackAssessmentZipCommandTests(KALiteTestCase):

    @patch.object(requests, "get", autospec=True)
    def test_command_with_url(self, get_method):
        url = "http://fakeurl.com/test.zip"

        with open(ASSESSMENT_ZIP_SAMPLE_PATH) as f:
            zip_raw_data = f.read()
            zf = zipfile.ZipFile(StringIO.StringIO(zip_raw_data))
            get_method.return_value = MagicMock(content=zip_raw_data)

            call_command("unpack_assessment_zip", url)

            get_method.assert_called_once_with(url)

            # verify that the assessment json just extracted is written to the khan data dir
            self.assertEqual(zf.open("assessment_items.json").read(),
                             open(mod.ASSESSMENT_ITEMS_PATH).read())

            # TODO(aron): write test for verifying that assessment items are combined
            # once the splitting code on the generate_assessment_zips side is written

            # verify that the other items are written to the content directory
            for filename in zf.namelist():
                # already verified above; no need to double-dip
                if "assessment_items.json" in filename:
                    continue
                else:
                    filename_path = os.path.join(mod.KHAN_CONTENT_PATH, filename)
                    self.assertTrue(os.path.exists(filename_path), "%s wasn't extracted to %s" % (filename, mod.KHAN_CONTENT_PATH))

    def test_command_with_local_path(self):
        pass


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

    @patch.object(zipfile, "ZipFile", autospec=True)
    def test_extract_assessment_items_to_data_dir(self, zipfile_class):
        with zipfile.ZipFile("mock.zip") as zf:
            mod.extract_assessment_items_to_data_dir(zf)

            self.assertTrue(zf.extract.call_args[0][0], "assessment_items.json")

    def test_is_valid_url_returns_true_for_valid_urls(self):
        valid_urls = [
            "http://stackoverflow.com/questions/25259134/how-can-i-check-whether-a-url-is-valid-using-urlparse",
            "http://en.wikipedia.org/wiki/Internationalized_resource_identifier"
        ]

        for url in valid_urls:
            self.assertTrue(mod.is_valid_url(url))
