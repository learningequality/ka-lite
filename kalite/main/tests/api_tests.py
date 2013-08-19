import json
import os

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest

import settings
from .base import MainTestCase
from .command_tests import VideoScanTests
from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser
from utils.testing.client import KALiteClient


class TestSaveExerciseLog(TestCase):
    
    ORIGINAL_POINTS = 37
    ORIGINAL_ATTEMPTS = 3
    ORIGINAL_STREAK_PROGRESS = 20
    NEW_POINTS_LARGER = 22
    NEW_STREAK_PROGRESS_LARGER = 10
    NEW_POINTS_SMALLER = 0
    NEW_STREAK_PROGRESS_SMALLER = 0
    EXERCISE_ID = "number_line"
    EXERCISE_ID2 = "radius_diameter_and_circumference"
    USERNAME = "testuser"
    PASSWORD = "dummy"
    
    def setUp(self):
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.USERNAME, facility=self.facility)
        self.user.set_password(self.PASSWORD)
        self.user.save()

        # create an initial ExerciseLog instance so we have something to update later
        self.original_exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user)
        self.original_exerciselog.points = self.ORIGINAL_POINTS
        self.original_exerciselog.attempts = self.ORIGINAL_ATTEMPTS
        self.original_exerciselog.streak_progress = self.ORIGINAL_STREAK_PROGRESS
        self.original_exerciselog.save()
    
    def test_new_exerciselog(self):
        
        # make sure the target exercise log does not already exist
        exerciselogs = ExerciseLog.objects.filter(exercise_id=self.EXERCISE_ID2, user__username=self.USERNAME)
        self.assertEqual(exerciselogs.count(), 0, "The target exercise log to be newly created already exists")

        c = KALiteClient()
        
        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")
        
        # save a new exercise log
        result = c.save_exercise_log(
            exercise_id=self.EXERCISE_ID2,
            streak_progress=self.NEW_STREAK_PROGRESS_LARGER,
            points=self.NEW_POINTS_LARGER,
            correct=True,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the exercise log." % result.status_code)
        
        # get a reference to the newly created ExerciseLog
        exerciselog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_ID2, user__username=self.USERNAME)
        
        # make sure the ExerciseLog was properly created
        self.assertEqual(exerciselog.points, self.NEW_POINTS_LARGER, "The ExerciseLog's points were not saved correctly.")
        self.assertEqual(exerciselog.streak_progress, self.NEW_STREAK_PROGRESS_LARGER, "The ExerciseLog's streak progress was not saved correctly.")
        self.assertEqual(exerciselog.attempts, 1, "The ExerciseLog did not have the correct number of attempts (1).")        

    def test_update_exerciselog(self):

        # get a new reference to the existing ExerciseLog
        exerciselog = ExerciseLog.objects.get(id=self.original_exerciselog.id)
        
        # make sure the ExerciseLog hasn't already been changed
        self.assertEqual(exerciselog.points, self.ORIGINAL_POINTS, "The ExerciseLog's points have already changed.")
        self.assertEqual(exerciselog.streak_progress, self.ORIGINAL_STREAK_PROGRESS, "The ExerciseLog's streak progress already changed.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS, "The ExerciseLog's attempts have already changed.")
        
        c = KALiteClient()
        
        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")
        
        # save a new record onto the exercise log, with a correct answer (increasing the points and streak)
        result = c.save_exercise_log(
            exercise_id=self.EXERCISE_ID,
            streak_progress=self.NEW_STREAK_PROGRESS_LARGER,
            points=self.NEW_POINTS_LARGER,
            correct=True,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the exercise log." % result.status_code)
        
        # get a reference to the updated ExerciseLog
        exerciselog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_ID, user__username=self.USERNAME)
        
        # make sure the ExerciseLog was properly updated
        self.assertEqual(exerciselog.points, self.NEW_POINTS_LARGER, "The ExerciseLog's points were not updated correctly.")
        self.assertEqual(exerciselog.streak_progress, self.NEW_STREAK_PROGRESS_LARGER, "The ExerciseLog's streak progress was not updated correctly.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS + 1, "The ExerciseLog did not have the correct number of attempts.")

        # save a new record onto the exercise log, with an incorrect answer (decreasing the points and streak)
        result = c.save_exercise_log(
            exercise_id=self.EXERCISE_ID,
            streak_progress=self.NEW_STREAK_PROGRESS_SMALLER,
            points=self.NEW_POINTS_SMALLER,
            correct=False,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the exercise log." % result.status_code)
        
        # get a reference to the updated ExerciseLog
        exerciselog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_ID, user__username=self.USERNAME)
        
        # make sure the ExerciseLog was properly updated
        self.assertEqual(exerciselog.points, self.NEW_POINTS_SMALLER, "The ExerciseLog's points were not saved correctly.")
        self.assertEqual(exerciselog.streak_progress, self.NEW_STREAK_PROGRESS_SMALLER, "The ExerciseLog's streak progress was not saved correctly.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS + 2, "The ExerciseLog did not have the correct number of attempts.")        


class TestSaveVideoLog(TestCase):
    
    ORIGINAL_POINTS = 84
    ORIGINAL_SECONDS_WATCHED = 32
    NEW_POINTS = 32
    NEW_SECONDS_WATCHED = 15
    YOUTUBE_ID = "aNqG4ChKShI"
    YOUTUBE_ID2 = "b22tMEc6Kko"
    USERNAME = "testuser"
    PASSWORD = "dummy"
    
    def setUp(self):
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.USERNAME, facility=self.facility)
        self.user.set_password(self.PASSWORD)
        self.user.save()
        
        # create an initial VideoLog instance so we have something to update later
        self.original_videolog = VideoLog(youtube_id=self.YOUTUBE_ID, user=self.user)
        self.original_videolog.points = self.ORIGINAL_POINTS
        self.original_videolog.total_seconds_watched = self.ORIGINAL_SECONDS_WATCHED
        self.original_videolog.save()

    def test_new_videolog(self):
        
        # make sure the target video log does not already exist
        videologs = VideoLog.objects.filter(youtube_id=self.YOUTUBE_ID2, user__username=self.USERNAME)
        self.assertEqual(videologs.count(), 0, "The target video log to be newly created already exists")

        c = KALiteClient()
        
        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")
        
        # save a new video log
        result = c.save_video_log(
            youtube_id=self.YOUTUBE_ID2,
            seconds_watched=self.NEW_SECONDS_WATCHED,
            points=self.NEW_POINTS,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)
        
        # get a reference to the newly created VideoLog
        videolog = VideoLog.objects.get(youtube_id=self.YOUTUBE_ID2, user__username=self.USERNAME)
        
        # make sure the VideoLog was properly created
        self.assertEqual(videolog.points, self.NEW_POINTS, "The VideoLog's points were not saved correctly.")
        self.assertEqual(videolog.total_seconds_watched, self.NEW_SECONDS_WATCHED, "The VideoLog's seconds watched was not saved correctly.")

    def test_update_videolog(self):

        # get a new reference to the existing VideoLog
        videolog = VideoLog.objects.get(id=self.original_videolog.id)
        
        # make sure the VideoLog hasn't already been changed
        self.assertEqual(videolog.points, self.ORIGINAL_POINTS, "The VideoLog's points have already changed.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED, "The VideoLog's seconds watched already changed.")
        
        c = KALiteClient()
        
        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")
        
        # save a new record onto the video log, with a correct answer (increasing the points and streak)
        result = c.save_video_log(
            youtube_id=self.YOUTUBE_ID,
            seconds_watched=self.NEW_SECONDS_WATCHED,
            points=self.ORIGINAL_POINTS + self.NEW_POINTS,
            correct=True,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)
        
        # get a reference to the updated VideoLog
        videolog = VideoLog.objects.get(youtube_id=self.YOUTUBE_ID, user__username=self.USERNAME)
        
        # make sure the VideoLog was properly updated
        self.assertEqual(videolog.points, self.ORIGINAL_POINTS + self.NEW_POINTS, "The VideoLog's points were not updated correctly.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED + self.NEW_SECONDS_WATCHED, "The VideoLog's seconds watched was not updated correctly.")


class TestAdminApiCalls(MainTestCase):
    """
    Test main.api_views that require an admin login
    """
    ADMIN_USERNAME = "testadmin"
    ADMIN_PASSWORD = "password"

    def __init__(self, *args, **kwargs):
        super(TestAdminApiCalls, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        """
        Create a superuser, then log in.  Add a fake video file.
        """
        super(TestAdminApiCalls, self).setUp(*args, **kwargs)

        call_command("createsuperuser", username=self.ADMIN_USERNAME, email="a@b.com", interactive=False)
        admin_user = User.objects.get(username=self.ADMIN_USERNAME)
        admin_user.set_password(self.ADMIN_PASSWORD)
        admin_user.save()

        # Choose, and create, a video
        self.fake_video_file, self.video_id = self.create_random_video_file()
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are no VideoFile objects, to start.")

        # login
        self.client = KALiteClient()
        success = self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        self.assertTrue(success, "Was not able to login as the admin user")

    def tearDown(self, *args, **kwargs):
        """
        Remove the fake video file.
        """
        super(TestAdminApiCalls, self).tearDown(*args, **kwargs)
        if os.path.exists(self.fake_video_file):
            os.remove(self.fake_video_file)


    def test_delete_non_existing_video(self):
        """
        "Delete" a video through the API that never existed.
        """
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

        # Delete a video file, make sure 
        result = self.client.delete_videos(youtube_ids=[self.video_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

    def test_delete_existing_video_object(self):
        """
        Delete a video through the API, when only the videofile object exists
        """
        VideoFile(youtube_id=self.video_id).save()
        os.remove(self.fake_video_file)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Should have 1 object; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

        # Delete a video file, make sure 
        result = self.client.delete_videos(youtube_ids=[self.video_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Should have 1 object; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")


    def test_delete_existing_video_file(self):
        """
        Delete a video through the API, when only the video exists on disk (not as an object)
        """
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertTrue(os.path.exists(self.fake_video_file), "Video file should exist on disk.")

        # Delete a video file, make sure 
        result = self.client.delete_videos(youtube_ids=[self.video_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")
