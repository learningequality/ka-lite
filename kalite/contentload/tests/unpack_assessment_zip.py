import StringIO
import json
import os
import requests
import tempfile
import zipfile
from mock import patch, MagicMock, mock_open

from django.conf import settings
from django.core.management import call_command

from kalite.testing import KALiteTestCase
from kalite.contentload.management.commands import unpack_assessment_zip as mod
from kalite import version


class UnpackAssessmentZipCommandTests(KALiteTestCase):

    def setUp(self):
        _, self.zipfile_path = tempfile.mkstemp()
        with open(self.zipfile_path, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            for dirpath, _, filenames in os.walk(os.path.join(os.path.dirname(__file__), "fixtures")):
                # this toplevel for loop should only do one loop, but
                # it's in a for loop nonetheless since it's more idiomatic
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    zf.write(full_path, filename)
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
            get_method.return_value = MagicMock(content=zip_raw_data)

            call_command(
                "unpack_assessment_zip",
                url,
                force_download=True  # always force the download, so we can be sure the get method gets called
            )

            get_method.assert_called_once_with(url)

            # verify that the assessment json just extracted is written to the khan data dir
            self.assertEqual(zf.open("assessmentitems.json").read(),
                             open(mod.ASSESSMENT_ITEMS_PATH).read())

            # TODO(aron): write test for verifying that assessment items are combined
            # once the splitting code on the generate_assessment_zips side is written

            # verify that the other items are written to the content directory
            for filename in zf.namelist():
                # already verified above; no need to double-dip
                if "assessmentitems.json" in filename:
                    continue
                else:
                    filename_path = os.path.join(mod.KHAN_CONTENT_PATH, filename)
                    self.assertTrue(os.path.exists(filename_path), "%s wasn't extracted to %s" % (filename, mod.KHAN_CONTENT_PATH))

    def test_command_with_local_path(self):
        pass


class UnpackAssessmentZipUtilityFunctionTests(KALiteTestCase):

    def setUp(self):
        _, self.zipfile_path = tempfile.mkstemp()
        with open(self.zipfile_path, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            for dirpath, _, filenames in os.walk(os.path.join(os.path.dirname(__file__), "fixtures")):
                # this toplevel for loop should only do one loop, but
                # it's in a for loop nonetheless since it's more idiomatic
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    zf.write(full_path, filename)
            zf.close()

    def tearDown(self):
        os.unlink(self.zipfile_path)

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

    @patch.object(version, 'SHORTVERSION', '0.13')
    def test_should_upgrade_assessment_items(self):
        # if assessmentitems.json.version doesn't exist, then return
        # true
        with patch("os.path.exists") as exists_method:
            exists_method.return_value = False
            self.assertTrue(
                mod.should_upgrade_assessment_items(),
                "We told our user not to download assessment items even if they don't have it! Madness!"
            )

        # if the version in assessmentitems.json.version is less
        # than our current version, then we should upgrade (return True)
        assessment_items_mock_version = "0.9.0"
        with patch('%s.open' % mod.__name__, mock_open(read_data=assessment_items_mock_version), create=True) as mopen:
            self.assertTrue(
                mod.should_upgrade_assessment_items(),
                "We should've told our users to upgrade assessment items, as they have an old version!"
            )
            # we should've also opened the file atleast
            mopen.assert_called_once_with(mod.ASSESSMENT_ITEMS_VERSION_PATH)

        # if the version in assessment items is equal to our current
        # version, then don't upgrade
        assessment_items_mock_version = version.SHORTVERSION
        with patch('%s.open' % mod.__name__, mock_open(read_data=assessment_items_mock_version), create=True) as mopen:
            self.assertFalse(
                mod.should_upgrade_assessment_items(),
                "We should not tell the user to upgrade when we have the same version as assessment items!"
            )
            # we should've also opened the file atleast
            mopen.assert_called_once_with(mod.ASSESSMENT_ITEMS_VERSION_PATH)


    def test_extract_assessment_items_to_data_dir(self):
        with open(mod.ASSESSMENT_ITEMS_PATH) as f:
            old_assessment_items = json.load(f)

        with open(self.zipfile_path) as f:
            zf = zipfile.ZipFile(f)
            mod.extract_assessment_items_to_data_dir(zf)
            zf.close()

        # test that it combines the new assessment items with the previous one
        with open(mod.ASSESSMENT_ITEMS_PATH) as f:
            items = json.load(f)

            for old_item in old_assessment_items:
                self.assertTrue(old_item in items)

            # test that there are new items in the assessment items too

        # test that it extract the assessment items version file
        self.assertTrue(os.path.exists(mod.ASSESSMENT_ITEMS_VERSION_PATH), "assessmentitems.json.version wasn't extracted!")

    def test_is_valid_url_returns_true_for_valid_urls(self):
        valid_urls = [
            "http://stackoverflow.com/questions/25259134/how-can-i-check-whether-a-url-is-valid-using-urlparse",
            "http://en.wikipedia.org/wiki/Internationalized_resource_identifier"
        ]

        for url in valid_urls:
            self.assertTrue(mod.is_valid_url(url))
