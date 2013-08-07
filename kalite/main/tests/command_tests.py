"""
"""
import os
import random

from django.core.management import call_command

import settings
from .base import MainTestCase
from main.models import VideoFile
from shared import caching


class VideoScanTests(MainTestCase):

    def setUp(self, *args, **kwargs):
        super(VideoScanTests, self).setUp(*args, **kwargs)

        # Choose, and create, a video
        self.fake_video_file, self.video_id = self.create_random_video_file()
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are no VideoFile objects, to start.")


    def test_video_added_no_cache(self):
        """
        Add a video, then call videoscan
        """

        # Call videoscan, and validate.
        out = call_command("videoscan", auto_cache=False)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Make sure there is now one VideoFile object.")
        self.assertEqual(VideoFile.objects.all()[0].youtube_id, self.video_id, "Make sure the video is the one we created.")
        self.assertEqual(self.web_cache._num_entries, 0, "Check that cache is empty.")


    def test_video_added_with_cache(self):
        """
        Add a video, then call videoscan
        """
        # Call videoscan, and validate.
        out = call_command("videoscan", auto_cache=True)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Make sure there is now one VideoFile object.")
        self.assertEqual(VideoFile.objects.all()[0].youtube_id, self.video_id, "Make sure the video is the one we created.")
        self.assertTrue(self.web_cache._num_entries > 0, "Check that cache is not empty.")
        cached_paths = caching.get_video_page_paths(video_id=self.video_id)
        for path in cached_paths:
            self.assertTrue(caching.has_cache_key(path), "Check that cache has path %s" % path)


    def test_video_deleted_no_cache(self):
        """
        Add a video, then call videoscan
        """
        self.test_video_added_no_cache()
        self.assertEqual(self.web_cache._num_entries, 0, "Check that cache is empty.")
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Choose, and create, a video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")
        self.assertTrue(self.web_cache._num_entries == 0, "Check that cache is empty (videoscan cleaned it).")



    def test_video_deleted_with_cache(self):
        """
        Add a video, then call videoscan
        """
        out = call_command("videoscan", auto_cache=True)
        cached_paths = caching.get_video_page_paths(video_id=self.video_id)
        for path in cached_paths:
            self.assertTrue(caching.has_cache_key(path), "Check that cache has path %s" % path)
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Choose, and create, a video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")
        for path in cached_paths:
            self.assertFalse(caching.has_cache_key(path), "Check that cache does NOT have path %s" % path)
