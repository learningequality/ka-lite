import os
import random

import settings
from main.topicdata import NODE_CACHE
from shared.testing.base import KALiteTestCase


class MainTestCase(KALiteTestCase):

    def create_random_video_file(self):
        """
        Helper function for testing video files.
        """
        youtube_id = NODE_CACHE.keys()[0]
        video_id = youtube_id
        fake_video_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id)
        with open(fake_video_file, "w") as fh:
            fh.write("")
        self.assertTrue(os.path.exists(fake_video_file), "Make sure the video file was created, youtube_id='%s'." % youtube_id)
        return (fake_video_file, video_id, youtube_id)

