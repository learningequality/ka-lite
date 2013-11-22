import os
import random

import settings
from main.topicdata import ID2SLUG_MAP
from shared.testing.base import KALiteTestCase


class MainTestCase(KALiteTestCase):

    def create_random_video_file(self):
        """
        Helper function for testing video files.
        """
        youtube_id = ID2SLUG_MAP.keys()[0]#random.choice(ID2SLUG_MAP.keys())
        fake_video_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id)
        with open(fake_video_file, "w") as fh:
            fh.write("")
        self.assertTrue(os.path.exists(fake_video_file), "Make sure the video file was created, youtube_id='%s'." % youtube_id)
        return (fake_video_file, youtube_id)

