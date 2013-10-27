"""
"""
import os
import random
import re

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import unittest

import settings
from .base import MainTestCase
from main.models import VideoFile
from securesync.models import Facility, FacilityUser
from shared import caching
from shared.testing.client import KALiteClient
from shared.testing.decorators import distributed_server_test
from utils.django_utils import call_command_with_output


@unittest.skipIf(settings.CACHE_TIME == 0, "Caching is disabled.")
@distributed_server_test
class VideoScanTests(MainTestCase):

    def setUp(self, *args, **kwargs):
        super(VideoScanTests, self).setUp(*args, **kwargs)

        # Choose, and create, a video
        self.fake_video_file, self.video_id = self.create_random_video_file()
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
        self.assertEqual(VideoFile.objects.all()[0].youtube_id, self.video_id, "Make sure the video is the one we created.")
        self.assertEqual(self.web_cache._num_entries, 0, "Check that cache is empty.")


    def test_video_added_with_cache(self):
        """
        Add a video in the filesystem, call videoscan to create the videofile object and cache items
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
        Run videoscan with a video file, but no cache items
        """
        self.test_video_added_no_cache()
        self.assertEqual(self.web_cache._num_entries, 0, "Check that cache is empty.")
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Remove the video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")
        self.assertTrue(self.web_cache._num_entries == 0, "Check that cache is empty (videoscan cleaned it).")



    def test_video_deleted_with_cache(self):
        """
        Run videoscan to create cache items, then re-run to verify that the cache is cleared.
        """
        out = call_command("videoscan", auto_cache=True)
        cached_paths = caching.get_video_page_paths(video_id=self.video_id)
        for path in cached_paths:
            self.assertTrue(caching.has_cache_key(path), "Check that cache has path %s" % path)
        self.assertTrue(os.path.exists(self.fake_video_file), "Check that video file exists.")

        # Remove the video
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Check that video file no longer exists.")

        # Call videoscan, and validate.
        out = call_command("videoscan")
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are now no VideoFile objects.")
        for path in cached_paths:
            self.assertFalse(caching.has_cache_key(path), "Check that cache does NOT have path %s" % path)


@distributed_server_test
class ChangeLocalUserPassword(MainTestCase):
    """Tests for the changelocalpassword command"""

    def setUp(self):
        """Create a new facility and facility user"""
        super(ChangeLocalUserPassword, self).setUp()

        self.old_password = 'testpass'
        self.username = "testuser"
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.username, facility=self.facility)
        self.user.set_password(self.old_password)
        self.user.save()


    def test_change_password_on_existing_user(self):
        """Change the password on an existing user."""

        # Now, re-retrieve the user, to check.
        (out,err,val) = call_command_with_output("changelocalpassword", self.user.username, noinput=True)
        self.assertEqual(err, "", "no output on stderr")
        self.assertNotEqual(out, "", "some output on stdout")
        self.assertEqual(val, 0, "Exit code is not zero")

        new_password =  re.search(r"Generated new password for user .*: '(?P<password>.*)'", out).group('password')
        self.assertNotEqual(self.old_password, new_password)

        c = KALiteClient()
        success = c.login(username=self.user.username, password=new_password, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")


    def test_change_password_on_nonexistent_user(self):
        nonexistent_username = "voiduser"
        with self.assertRaises(CommandError):
            (out, err, val) = call_command_with_output("changelocalpassword", nonexistent_username, noinput=True)
