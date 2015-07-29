import copy
import StringIO
import os
import requests
import tempfile
import zipfile
from mock import patch, MagicMock, mock_open

from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings

from kalite.testing.base import KALiteTestCase
from kalite.contentload.management.commands import unpack_assessment_zip as mod
from kalite import version

TEMP_CONTENT_PATH = tempfile.mkdtemp()
TEMP_ASSESSMENT_ITEM_DATABASE_PATH = os.path.join(TEMP_CONTENT_PATH, 'assessmentitems.sqlite')
TEMP_ASSESSMENT_ITEM_VERSION_PATH = os.path.join(TEMP_CONTENT_PATH, 'assessmentitems.version')
TEMP_ASSESSMENT_ITEM_JSON_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "assessmentitems.json")
DUMMY_ASSESSMENT_ITEM_DATABASE_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "assessmentitems.dummydb")

MODIFIED_DB_SETTINGS = copy.deepcopy(settings.DATABASES)
MODIFIED_DB_SETTINGS["assessment_items"]["NAME"] = TEMP_ASSESSMENT_ITEM_DATABASE_PATH


from kalite.contentload import settings as contentload_settings


# Patch up all these settings because settings are initialized and then
# overwritten after
contentload_settings.ASSESSMENT_ITEM_ROOT = TEMP_CONTENT_PATH
contentload_settings.KHAN_ASSESSMENT_ITEM_ROOT = TEMP_CONTENT_PATH
contentload_settings.KHAN_ASSESSMENT_ITEM_DATABASE_PATH = os.path.join(TEMP_CONTENT_PATH, 'assessmentitems.sqlite')
# Default locations of specific elements from the assessment items bundle.
# Files will be forced into this location when running unpack_assessment_zip
contentload_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH = os.path.join(TEMP_CONTENT_PATH, 'assessmentitems.version')
contentload_settings.KHAN_ASSESSMENT_ITEM_JSON_PATH = os.path.join(TEMP_CONTENT_PATH, 'assessmentitems.json')


@override_settings(CONTENT_ROOT=TEMP_CONTENT_PATH)
class UnpackAssessmentZipCommandTests(KALiteTestCase):

    def setUp(self):
        
        # Create a dummy assessment item zip
        _, self.zipfile_path = tempfile.mkstemp()
        with open(self.zipfile_path, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            zf.write(DUMMY_ASSESSMENT_ITEM_DATABASE_SOURCE_PATH, "assessmentitems.sqlite")
            zf.writestr("assessmentitems.version", version.SHORTVERSION)
            zf.close()

    def tearDown(self):
        os.unlink(self.zipfile_path)

    @patch("%s.open" % mod.__name__, mock_open(), create=True)
    @patch.object(requests, "get")
    @patch.object(mod, "should_upgrade_assessment_items")
    def test_command_should_skip(self, upgrade_method, get_method):
        upgrade_method.return_value = False

        # test that we don't update when given a url
        url = "http://fakeurl.com/test.zip"
        call_command("unpack_assessment_zip", url)
        self.assertEqual(get_method.call_count, 0, "requests.get was called even if we should've skipped!")

        filename = "/fake/file/somewhere.zip"
        call_command("unpack_assessment_zip", filename)
        self.assertEqual(mod.open.call_count, 0,  "open was called even if we should've skipped!")

    @patch.object(requests, "get", autospec=True)
    def test_command_with_url(self, get_method):
        url = "http://fakeurl.com/test.zip"

        with open(self.zipfile_path) as f:
            zip_raw_data = f.read()
            zf = zipfile.ZipFile(StringIO.StringIO(zip_raw_data))
            get_method.return_value.iter_content = MagicMock(return_value=zip_raw_data)

            call_command(
                "unpack_assessment_zip",
                url,
                force_download=True  # always force the download, so we can be sure the get method gets called
            )

            get_method.assert_called_once_with(url, prefetch=False)

            # TODO(aron): write test for verifying that assessment items are combined
            # once the splitting code on the generate_assessment_zips side is written

            # verify that the other items are written to the content directory
            for filename in zf.namelist():
                # already verified above; no need to double-dip
                if "assessmentitems" in filename:
                    continue
                else:
                    filename_path = os.path.join(mod.CONTENT_ROOT, filename)
                    self.assertTrue(os.path.exists(filename_path), "%s wasn't extracted to %s" % (filename, mod.CONTENT_ROOT))

    def test_command_with_local_path(self):
        pass


@override_settings(CONTENT_ROOT=TEMP_CONTENT_PATH)
class UnpackAssessmentZipUtilityFunctionTests(KALiteTestCase):

    def setUp(self):
        _, self.zipfile_path = tempfile.mkstemp()
        with open(self.zipfile_path, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            zf.write(DUMMY_ASSESSMENT_ITEM_DATABASE_SOURCE_PATH, "assessmentitems.sqlite")
            zf.writestr("assessmentitems.version", version.SHORTVERSION)
            zf.close()

        call_command(
            "unpack_assessment_zip",
            self.zipfile_path,
        )

    def tearDown(self):
        os.unlink(self.zipfile_path)

    def test_unpack_zipfile_to_khan_content_extracts_to_content_dir(self):
        zipfile_instance = MagicMock()
        
        from kalite.contentload.settings import KHAN_ASSESSMENT_ITEM_ROOT
        extract_dir = KHAN_ASSESSMENT_ITEM_ROOT

        mod.unpack_zipfile_to_khan_content(zipfile_instance)

        zipfile_instance.extractall.assert_called_once_with(extract_dir)

    def test_is_valid_url_returns_false_for_invalid_urls(self):
        invalid_urls = [
            "/something.path",
            "/path/to/somewhere"
        ]

        for url in invalid_urls:
            self.assertFalse(mod.is_valid_url(url))

    @patch.object(version, 'SHORTVERSION', '0.14')
    def test_should_upgrade_assessment_items(self):
        # if assessmentitems.version doesn't exist, then return
        # true
        with patch("os.path.exists") as exists_method:
            exists_method.return_value = False
            self.assertTrue(
                mod.should_upgrade_assessment_items(),
                "We told our user not to download assessment items even if they don't have it! Madness!"
            )

        # if the version in assessmentitems.version is less
        # than our current version, then we should upgrade (return True)
        assessment_items_mock_version = "0.9.0"
        with patch('%s.open' % mod.__name__, mock_open(read_data=assessment_items_mock_version), create=True) as mopen:
            self.assertTrue(
                mod.should_upgrade_assessment_items(),
                "We should've told our users to upgrade assessment items, as they have an old version!"
            )
            # we should've also opened the file at least
            mopen.assert_called_once_with(contentload_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH)

        # if the version in assessment items is equal to our current
        # version, then don't upgrade
        assessment_items_mock_version = version.SHORTVERSION
        with patch('%s.open' % mod.__name__, mock_open(read_data=assessment_items_mock_version), create=True) as mopen:
            self.assertFalse(
                mod.should_upgrade_assessment_items(),
                "We should not tell the user to upgrade when we have the same version as assessment items!"
            )
            # we should've also opened the file atleast
            mopen.assert_called_once_with(contentload_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH)

    def test_is_valid_url_returns_true_for_valid_urls(self):
        valid_urls = [
            "http://stackoverflow.com/questions/25259134/how-can-i-check-whether-a-url-is-valid-using-urlparse",
            "http://en.wikipedia.org/wiki/Internationalized_resource_identifier"
        ]

        for url in valid_urls:
            self.assertTrue(mod.is_valid_url(url))
