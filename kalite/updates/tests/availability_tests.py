import glob
import os

from django.conf import settings

from .base import UpdatesTestCase
from kalite.topic_tools.content_models import get_content_items, get_topic_nodes

class TestTopicAvailability(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def setUp(self):
        super(TestTopicAvailability, self).setUp()
        self.n_content = len(glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4")))

    def test_topic_availability(self):
        nodes = get_content_items()
        for topic in nodes:
            if topic.get("kind") == "Topic":
                any_available = any([item.get("available", False) for item in get_topic_nodes(parent=topic.get("id"))])
                self.assertEqual(topic["available"], any_available, "Topic availability for {topic} did not match child availability when any children are available.".format(topic=topic.get("title")))
