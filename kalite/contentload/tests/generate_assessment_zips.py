import json
import os
import requests
from mock import patch, MagicMock

from django.core.management import call_command

from kalite.testing import KALiteTestCase
from kalite.contentload.management.commands import generate_assessment_zips as mod

HTTREPLAY_RECORDINGS_DIR = os.path.join(os.path.dirname(__file__),
                                        "fixtures")


class GenerateAssessmentItemsCommandTests(KALiteTestCase):

    @patch.object(requests, 'get')
    def test_fetches_assessment_items(self, get_method):
        with open(os.path.join(HTTREPLAY_RECORDINGS_DIR, "assessment_items_cache.json")) as f:
            assessment_items_content = f.read()

        get_method.return_value = MagicMock(content=assessment_items_content)

        call_command("generate_assessment_zips")

        self.assertEqual(get_method.call_count, 1, "requests.get not called at all!")


class UtilityFunctionTests(KALiteTestCase):

    def setUp(self):

        with open(os.path.join(HTTREPLAY_RECORDINGS_DIR, "assessment_items_sample.json")) as f:
            self.assessment_sample = json.load(f)
        self.imgurl = "https://ka-perseus-graphie.s3.amazonaws.com/8ea5af1fa5a5e8b8e727c3211083111897d23f5d.png"

    def test_gets_images_urls_inside_item_data(self):

        result = list(mod.all_image_urls(self.assessment_sample))
        self.assertIn(
            self.imgurl,
            result,
            "%s not found!" % self.imgurl
        )

    def test_localhosted_image_urls_replaces_with_local_urls(self):
        newimgurl = "http://localhost:8008/8ea5af1fa5a5e8b8e727c3211083111897d23f5d.png"  # replace with what's in settings
        new_assessment_items = mod.localhosted_image_urls(self.assessment_sample)

        all_images = list(mod.all_image_urls(new_assessment_items))
        self.assertNotIn(self.imgurl, all_images)
        self.assertIn(newimgurl, all_images)
