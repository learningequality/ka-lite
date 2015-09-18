import json
import os
import requests
import shutil
import tempfile
import zipfile
from fle_utils.general import ensure_dir
from mock import patch, MagicMock

from django.test import TestCase

import kalite.version as version
from kalite.testing.base import KALiteTestCase
from kalite.contentload.management.commands import generate_assessment_zips as mod


TEST_FIXTURES_DIR = os.path.join(os.path.dirname(__file__),
                                        "fixtures")
ASSESSMENT_ITEMS_SAMPLE_PATH = os.path.join(TEST_FIXTURES_DIR,
                                            "assessment_items_sample.json")

class TestUrlConversion(TestCase):

    def setUp(self):
        with open(ASSESSMENT_ITEMS_SAMPLE_PATH) as f:
            self.assessment_items = json.load(f)
    
    def test_image_url_converted(self):
        url_string = "A string with http://example.com/cat_pics.gif"
        expected_string = "A string with /content/khan/cat/cat_pics.gif"
        self.assertEqual(expected_string, mod.convert_urls(url_string))
    
    def test_multiple_image_urls_in_one_string_converted(self):
        url_string = "A string with http://example.com/cat_pics.JPEG http://example.com/cat_pics2.gif"
        expected_string = "A string with /content/khan/cat/cat_pics.JPEG /content/khan/cat/cat_pics2.gif"
        self.assertEqual(expected_string, mod.convert_urls(url_string))

    def test_content_link_converted(self):
        link_string = "(and so that is the correct answer).**\\n\\n[Watch this video to review](https://www.khanacademy.org/humanities/history/ancient-medieval/Ancient/v/standard-of-ur-c-2600-2400-b-c-e)"
        expected_string = "(and so that is the correct answer).**\\n\\n[Watch this video to review](/learn/khan/test-prep/ap-art-history/ancient-mediterranean-ap/ancient-near-east-a/standard-of-ur-c-2600-2400-b-c-e/)"
        self.assertEqual(expected_string, mod.convert_urls(link_string))

    def test_bad_content_link_removed(self):
        link_string = "Wrong!\n\n**[Watch video to review](https://www.khanacademy.org/humanities/art-history/v/the-penguin-king-has-risen)**\n\nThat's a wrap!"
        expected_string = "Wrong!\n\n\n\nThat's a wrap!"
        self.assertEqual(expected_string, mod.convert_urls(link_string))

    def test_localize_all_image_urls(self):
        new_items = mod.localize_all_image_urls(self.assessment_items)
        old_item_data = self.assessment_items.values()[0]["item_data"]
        new_item_data = new_items.values()[0]["item_data"]
        self.assertNotIn("https://ka-perseus", new_item_data)

    def test_localize_all_content_links(self):
        new_items = mod.localize_all_content_links(self.assessment_items)
        old_item_data = self.assessment_items.values()[0]["item_data"]
        new_item_data = new_items.values()[0]["item_data"]
        self.assertEqual(old_item_data.replace(
            "https://www.khanacademy.org/math/early-math/cc-early-math-add-sub-topic/basic-addition-subtraction/v/addition-introduction",
            "/learn/khan/math/early-math/cc-early-math-add-sub-basics/cc-early-math-add-sub-intro/addition-introduction/"), new_item_data)
        self.assertNotIn("khanacademy.org", new_item_data)

    def test_localize_all_graphie_urls(self):
        new_items = mod.localize_all_graphie_urls(self.assessment_items)
        old_item_data = self.assessment_items.values()[0]["item_data"]
        new_item_data = new_items.values()[0]["item_data"]
        self.assertNotIn("web+graphie://ka-perseus", new_item_data)


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

    # TODO(jamalex): This is disabled because I couldn't get init_assessment_items (called by generate_assessment_zips)
    # to write to a sqlite file instead of to the :memory: store used for testing
    # @override_settings(ASSESSMENT_ITEM_JSON_PATH=ASSESSMENT_ITEMS_SAMPLE_PATH)
    # @patch.object(requests, 'get')
    # def test_command(self, get_method):

    #     with open(ASSESSMENT_ITEMS_SAMPLE_PATH) as f:
    #         assessment_items_content = f.read()

    #     image_requests = len(set(list(mod.find_all_image_urls(json.loads(assessment_items_content)))
    #                            + list(mod.find_all_graphie_urls(json.loads(assessment_items_content)))))

    #     get_method.return_value = MagicMock(content=assessment_items_content)

    #     call_command("generate_assessment_zips")

    #     self.assertEqual(get_method.call_count, image_requests, "requests.get not called the correct # of times!")

    #     with open(mod.ZIP_FILE_PATH) as f:
    #         zf = zipfile.ZipFile(mod.ZIP_FILE_PATH)
    #         self.assertIn("assessmentitems.sqlite", zf.namelist())  # make sure assessment items is written

    #         for filename in zf.namelist():
    #             if filename.lower().endswith(".gif"):
    #                 continue
    #             elif filename.lower().endswith(".jpg"):
    #                 continue
    #             elif filename.lower().endswith(".jpeg"):
    #                 continue
    #             elif filename.lower().endswith(".png"):
    #                 continue
    #             elif filename.lower().endswith(".svg"):
    #                 continue
    #             elif filename.lower().endswith("-data.json"):
    #                 continue
    #             elif filename in ["assessmentitems.sqlite", "assessmentitems.version"]:
    #                 continue
    #             else:
    #                 self.assertTrue(False, "Invalid file %s got in the assessment zip!" % filename)
    #         zf.close()


class UtilityFunctionTests(KALiteTestCase):

    def setUp(self):
        with open(os.path.join(TEST_FIXTURES_DIR, "assessment_items_sample.json")) as f:
            self.assessment_sample = json.load(f)

        self.imgurl = "https://ka-perseus-graphie.s3.amazonaws.com/8ea5af1fa5a5e8b8e727c3211083111897d23f5d.png"

    @patch.object(zipfile, "ZipFile", autospec=True)
    def test_write_assessment_item_version_to_zip(self, zipfile_class):
        with open(mod.ZIP_FILE_PATH, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            mod.write_assessment_item_version_to_zip(zf)

            zf.writestr.assert_called_once_with("assessmentitems.version", version.SHORTVERSION)

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
        get_method.assert_called_once_with(self.imgurl, timeout=10)
        self.assertTrue(os.path.exists(cached_file_path), "File wasn't cached!")

        get_method.call_count = 0
        # now test that we don't download that file again
        mod.fetch_file_from_url_or_cache(self.imgurl)
        self.assertEqual(get_method.call_count, 0, "requests.get called! File wasn't cached!")

    def test_gets_images_urls_inside_item_data(self):

        result = list(mod.find_all_image_urls(self.assessment_sample))
        self.assertIn(
            self.imgurl,
            result,
            "%s not found!" % self.imgurl
        )

    def test_localize_all_image_urls_replaces_with_local_urls(self):
        new_assessment_items = mod.localize_all_image_urls(self.assessment_sample)

        all_images = list(mod.find_all_image_urls(new_assessment_items))
        self.assertNotIn(self.imgurl, all_images)

    @patch.object(requests, "get")
    def test_download_url_to_zip_writes_to_zipfile(self, get_method):
        expected_return_value = "none"

        zipobj = MagicMock()

        get_method.return_value = MagicMock(content=expected_return_value)

        mod.download_url_to_zip(zipobj, "http://test.com/3497945345.gif")

        zipobj.writestr.assert_called_once_with("349/3497945345.gif", expected_return_value)

    @patch.object(zipfile, "ZipFile", autospec=True)
    @patch.object(mod, "download_url_to_zip")
    def test_download_url_downloads_all_urls(self, download_method, zipfile_class):
        download_method.return_value = 1

        urls = ["http://test1.com", "http://test2.com"]
        with open(mod.ZIP_FILE_PATH, "w") as f:
            zf = zipfile.ZipFile(f, "w")
            mod.download_urls_to_zip(zf, urls)
            zf.close()

        self.assertEqual(download_method.call_count, len(urls))
