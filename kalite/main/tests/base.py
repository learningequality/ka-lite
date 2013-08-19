import os
import random

import settings
from main.topicdata import ID2SLUG_MAP
from utils.testing.base import KALiteTestCase


class MainTestCase(KALiteTestCase):

    def create_random_video_file(self):
        """
        Helper function for testing video files.
        """
        video_id = ID2SLUG_MAP.keys()[0]#random.choice(ID2SLUG_MAP.keys())
        fake_video_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % video_id)
        with open(fake_video_file, "w") as fh:
            fh.write("")
        self.assertTrue(os.path.exists(fake_video_file), "Make sure the video file was created, video_id='%s'." % video_id)
        return (fake_video_file, video_id)

