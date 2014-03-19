import glob
import os

from django.conf import settings
from django.utils import unittest

from .base import UpdatesTestCase
from main.topic_tools import get_node_cache, get_topic_tree
from updates import stamp_availability_on_topic


class TestTopicAvailability(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def setUp(self):
        super(TestTopicAvailability, self).setUp()
        self.n_videos = len(glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4")))

    def test_video_availability(self):
        nvids_local = sum([node_list[0]["on_disk"] for node_list in get_node_cache("Video").values()])
        self.assertEqual(self.n_videos, nvids_local, "# videos actually on disk should match # videos in topic tree")

    def test_topic_availability(self):

        for node_list in get_node_cache("Topic").values():
            for topic in node_list:
                if "Exercise" in topic["contains"]:
                    self.assertTrue(topic["available"], "Make sure all topics containing exercises are shown as available.")
                if topic["children"] and len(topic["contains"]) == 1 and "Video" in topic["contains"]:
                    any_on_disk = bool(sum([v["on_disk"] for v in topic["children"]]))
                    self.assertEqual(topic["available"], any_on_disk, "Make sure topic availability matches video availability when only videos are available.")

