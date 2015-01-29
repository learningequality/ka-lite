import json
import os
import requests
import shutil
import tempfile
import zipfile
from fle_utils.general import ensure_dir
from mock import patch, MagicMock

from django.core.management import call_command

from kalite.testing import KALiteTestCase
from kalite.contentload.management.commands import generate_assessment_zips as mod

TEST_FIXTURES_DIR = os.path.join(os.path.dirname(__file__),
                                        "fixtures")
ASSESSMENT_ITEMS_SAMPLE_PATH = os.path.join(TEST_FIXTURES_DIR,
                                            "assessment_items_sample.json")


class GenerateAssessmentItemsCommandTests(KALiteTestCase):

    def setUp(self):
        self.tempdir_patch = patch.object(tempfile, "gettempdir")
        self.addCleanup(self.tempdir_patch.stop)
        self.gettempdir_method = self.tempdir_patch.start()

        # make sure we control the temp dir where temporary images are written
        self.fake_temp_dir = self.gettempdir_method.return_value = os.path.abspath("tmp/")
        ensure_dir(self.fake_temp_dir)

    def tearDown(self):
        shutil.rmtree(self.fake_temp_dir)

    @patch.object(mod, "ASSESSMENT_ITEMS_PATH", ASSESSMENT_ITEMS_SAMPLE_PATH)
    @patch.object(requests, 'get')
    def test_command(self, get_method):

        with open(ASSESSMENT_ITEMS_SAMPLE_PATH) as f:
            assessment_items_content = f.read()

        image_requests = len(set(mod.all_image_urls(json.loads(assessment_items_content))))

        get_method.return_value = MagicMock(content=assessment_items_content)

        call_command("generate_assessment_zips")

        self.assertEqual(get_method.call_count, image_requests, "requests.get not called the correct # of times!")


        with open(mod.ZIP_FILE_PATH) as f:
            zf = zipfile.ZipFile(mod.ZIP_FILE_PATH)
            self.assertIn("assessmentitems.json", zf.namelist())  # make sure assessment items is written

            for filename in zf.namelist():
                if ".gif" in filename:
                    continue
                elif ".jpg" in filename:
                    continue
                elif ".png" in filename:
                    continue
                elif "assessmentitems.json" in filename:
                    continue
                else:
                    self.assertTrue(False, "Invalid file %s got in the assessment zip!" % filename)
            zf.close()


class UtilityFunctionTests(KALiteTestCase):

    def setUp(self):
        with open(os.path.join(TEST_FIXTURES_DIR, "assessment_items_sample.json")) as f:
            self.assessment_sample = json.load(f)

        self.imgurl = "https://ka-perseus-graphie.s3.amazonaws.com/8ea5af1fa5a5e8b8e727c3211083111897d23f5d.png"

    @patch.object(zipfile, "ZipFile", autospec=True)
    def test_write_assessment_json_to_zip(self, zipfile_class):
        with open(mod.ZIP_FILE_PATH) as f:
            zf = zipfile.ZipFile(mod.ZIP_FILE_PATH)
            mod.write_assessment_to_zip(zf, self.assessment_sample)

            self.assertEqual(zf.writestr.call_args[0][0]  # call_args[0] are the positional arguments
                             , "assessmentitems.json")
            zf.close()

    @patch.object(requests, "get")
    def test_fetch_file_from_url_or_cache(self, get_method):
        expected_content = get_method.return_value.content = "testtest"

        # test that a nonexistent cache file is downloaded
        filename = os.path.basename(self.imgurl)
        cached_file_path = os.path.join(tempfile.tempdir, filename)
        if os.path.exists(cached_file_path):
            os.remove(cached_file_path)  # make sure it doesn't exist

        mod.fetch_file_from_url_or_cache(self.imgurl)
        get_method.assert_called_once_with(self.imgurl)
        self.assertTrue(os.path.exists(cached_file_path), "File wasn't cached!")

        get_method.call_count = 0
        # now test that we don't download that file again
        mod.fetch_file_from_url_or_cache(self.imgurl)
        self.assertEqual(get_method.call_count, 0, "requests.get called! File wasn't cached!")



    def test_gets_images_urls_inside_item_data(self):

        result = list(mod.all_image_urls(self.assessment_sample))
        self.assertIn(
            self.imgurl,
            result,
            "%s not found!" % self.imgurl
        )

    def test_localhosted_image_urls_replaces_with_local_urls(self):
        new_assessment_items = mod.localhosted_image_urls(self.assessment_sample)

        all_images = list(mod.all_image_urls(new_assessment_items))
        self.assertNotIn(self.imgurl, all_images)

    @patch.object(requests, "get")
    def test_download_url_to_zip_writes_to_zipfile(self, get_method):
        expected_return_value = "none"

        zipobj = MagicMock()

        get_method.return_value = MagicMock(content=expected_return_value)

        mod.download_url_to_zip(zipobj, "http://test.com")

        zipobj.writestr.assert_called_once_with("test.com", expected_return_value)

    @patch.object(zipfile, "ZipFile", autospec=True)
    @patch.object(mod, "download_url_to_zip")
    def test_download_url_downloads_all_urls(self, download_method, zipfile_class):
        download_method.return_value = 1

        urls = ["http://test1.com", "http://test2.com"]
        with open(mod.ZIP_FILE_PATH) as f:
            zf = zipfile.ZipFile(mod.ZIP_FILE_PATH)
            mod.download_urls(zf, urls)
            zf.close()

        self.assertEqual(download_method.call_count, len(urls))
