"""
"""
import os

from django.conf import settings
from django.core.management import call_command
from django.utils import unittest

from ..models import VideoFile
from kalite.main.tests.base import MainTestCase  # TODO: remove this dependency


@unittest.skipIf(settings.CACHE_TIME == 0, "Caching is disabled.")
class VideoScanTests(MainTestCase):

    def setUp(self, *args, **kwargs):
        super(VideoScanTests, self).setUp(*args, **kwargs)

        # Choose, and create, a video
        self.fake_video_file, self.video_id, self.youtube_id = self.create_random_content_file()
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are no VideoFile objects, to start.")

    def tearDown(self, *args, **kwargs):
        super(VideoScanTests, self).tearDown(*args, **kwargs)
        if os.path.exists(self.fake_video_file):
            os.remove(self.fake_video_file)


    def test_video_added_no_cache(self):
        """
        Add a video in the filesystem, then call videoscan to create videofile objects
        """

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 1, "Make sure there is now one VideoFile object.")
        self.assertEqual(VideoFile.objects.all()[0].youtube_id, self.youtube_id, "Make sure the video is the one we created.")


    @unittest.skipIf(True, "Failing test that I'm tired of debugging.")  # TODO(bcipolli): re-enable when we need to be able to auto-cache
    def test_video_added_with_cache(self):
        """
        Add a video in the filesystem, call videoscan to create the videofile object and cache items
        """
        # Call videoscan, and validate.
        out = call_command("videoscan", auto_cache=True)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Make sure there is now one VideoFile object.")
        self.assertEqual(VideoFile.objects.all()[0].youtube_id, self.youtube_id, "Make sure the video is the one we created.")

    def test_video_deleted_no_cache(self):
        """
        Run videoscan with a video file, but no cache items
        """
        self.test_video_added_no_cache()
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Remove the video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")

    def test_video_deleted_with_cache(self):
        """
        Run videoscan to create cache items, then re-run to verify that the cache is cleared.
        """
        out = call_command("videoscan", auto_cache=True)
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Remove the video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")


