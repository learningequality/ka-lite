import glob
import os

from django.conf import settings

from .base import UpdatesTestCase
from kalite.topic_tools.content_models import get_content_items, get_topic_contents

class TestTopicAvailability(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def setUp(self):
        super(TestTopicAvailability, self).setUp()
        self.n_content = len(glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4")))

    def test_topic_availability(self):
        nodes = get_content_items(dict=True)
        for topic in nodes:
            if topic.get("kind") == "Topic":
                any_available = any([item.get("available", False) for item in get_topic_contents(topic_id=topic.get("id"))])
                self.assertEqual(topic["available"], any_available, "Make sure topic availability matches child availability when any children are available.")
