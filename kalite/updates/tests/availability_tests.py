import glob
import os

from django.conf import settings

from .base import UpdatesTestCase
from kalite.topic_tools import get_content_cache, get_node_cache

class TestTopicAvailability(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def setUp(self):
        super(TestTopicAvailability, self).setUp()
        self.n_content = len(glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4")))

    def test_video_availability(self):
        ncontent_local = sum([len(node.get("languages", [])) for node in get_content_cache().values()])
        self.assertTrue(self.n_content >= ncontent_local, "# videos actually on disk should be >= # videos in topic tree")

    def test_topic_availability(self):
        for topic in get_node_cache("Topic").values():
            if topic.get("kind") == "Topic":
                any_available = bool(sum([get_node_cache("Topic").get(v, {}).get("available", False) for v in topic.get("children", [])]))
                self.assertEqual(topic["available"], any_available, "Make sure topic availability matches child availability when any children are available.")
