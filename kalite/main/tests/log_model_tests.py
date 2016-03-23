from django.utils import unittest

from ..models import VideoLog, ExerciseLog
from kalite.facility.models import Facility, FacilityUser
from kalite.testing.base import KALiteTestCase


class TestExerciseLogs(KALiteTestCase):

    ORIGINAL_POINTS = 37
    ORIGINAL_ATTEMPTS = 3
    NEW_POINTS = 22
    NEW_ATTEMPTS = 5
    EXERCISE_ID = "number_line"

    def setUp(self):
        super(TestExerciseLogs, self).setUp()

        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username="testuser", facility=self.facility)
        self.user.set_password("dumber")
        self.user.save()

        # create an initial ExerciseLog instance so we have something to collide with later
        self.original_exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user)
        self.original_exerciselog.points = self.ORIGINAL_POINTS
        self.original_exerciselog.attempts = self.ORIGINAL_ATTEMPTS
        self.original_exerciselog.save()

        # get a new reference to the existing ExerciseLog
        exerciselog = ExerciseLog.objects.get(id=self.original_exerciselog.id)

        # make sure the ExerciseLog was saved as intended
        self.assertEqual(exerciselog.points, self.ORIGINAL_POINTS, "The ExerciseLog's points have already changed.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS, "The ExerciseLog's attempts have already changed.")

    def test_exerciselog_update(self):

        # get a new reference to the existing ExerciseLog
        exerciselog = ExerciseLog.objects.get(id=self.original_exerciselog.id)

        # update the ExerciseLog
        exerciselog.points = self.NEW_POINTS
        exerciselog.attempts = self.NEW_ATTEMPTS
        exerciselog.save()

        # get a new reference to the existing ExerciseLog
        exerciselog2 = ExerciseLog.objects.get(id=self.original_exerciselog.id)

        # make sure the ExerciseLog was updated
        self.assertEqual(exerciselog2.points, self.NEW_POINTS, "The ExerciseLog's points were not updated.")
        self.assertEqual(exerciselog2.attempts, self.NEW_ATTEMPTS, "The ExerciseLog's attempts were not updated.")

    @unittest.skip("Auto-merging is not yet automatic, so skip this")
    def test_exerciselog_collision(self):

        # create a new exercise log with the same exercise_id and user, but different points/attempts
        exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user)
        exerciselog.points = self.NEW_POINTS
        exerciselog.attempts = self.NEW_ATTEMPTS

        # try saving the new ExerciseLog: this is where the collision will happen, hopefully leading to a merge
        exerciselog.save()

        # get a new reference to the existing ExerciseLog
        exerciselog2 = ExerciseLog.objects.get(id=self.original_exerciselog.id)

        # make sure the ExerciseLog has been properly merged
        self.assertEqual(exerciselog.points, max(self.ORIGINAL_POINTS, self.NEW_POINTS), "The ExerciseLog's points were not properly merged.")
        self.assertEqual(exerciselog.attempts, max(self.ORIGINAL_ATTEMPTS, self.NEW_ATTEMPTS), "The ExerciseLog's attempts have already changed.")


class TestVideoLogs(KALiteTestCase):

    ORIGINAL_POINTS = 37
    ORIGINAL_SECONDS_WATCHED = 3
    NEW_POINTS = 22
    NEW_SECONDS_WATCHED = 5
    YOUTUBE_ID = "aNqG4ChKShI"
    VIDEO_ID = "dummy"

    def setUp(self):
        super(TestVideoLogs, self).setUp()
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username="testuser", facility=self.facility)
        self.user.set_password("dumber")
        self.user.save()

        # create an initial VideoLog instance so we have something to collide with later
        self.original_videolog = VideoLog(video_id=self.VIDEO_ID, youtube_id=self.YOUTUBE_ID, user=self.user)
        self.original_videolog.points = self.ORIGINAL_POINTS
        self.original_videolog.total_seconds_watched = self.ORIGINAL_SECONDS_WATCHED
        self.original_videolog.save()

        # get a new reference to the existing VideoLog
        videolog = VideoLog.objects.get(id=self.original_videolog.id)

        # make sure the VideoLog was created correctly
        self.assertEqual(videolog.points, self.ORIGINAL_POINTS, "The VideoLog's points have already changed.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED, "The VideoLog's total seconds watched have already changed.")

    def test_videolog_update(self):

        # get a new reference to the existing VideoLog
        videolog = VideoLog.objects.get(id=self.original_videolog.id)

        # update the VideoLog
        videolog.points = self.NEW_POINTS
        videolog.total_seconds_watched = self.NEW_SECONDS_WATCHED
        videolog.save()

        # get a new reference to the existing VideoLog
        videolog2 = VideoLog.objects.get(id=self.original_videolog.id)

        # make sure the VideoLog was updated
        self.assertEqual(videolog2.points, self.NEW_POINTS, "The VideoLog's points were not updated.")
        self.assertEqual(videolog2.total_seconds_watched, self.NEW_SECONDS_WATCHED, "The VideoLog's total seconds watched were not updated.")

    @unittest.skip("Auto-merging is not yet automatic, so skip this")
    def test_videolog_collision(self):

        # create a new video log with the same youtube_id and user, but different points/total seconds watched
        videolog = VideoLog(video_id=self.VIDEO_ID, youtube_id=self.YOUTUBE_ID, user=self.user)
        videolog.points = self.NEW_POINTS
        videolog.total_seconds_watched = self.NEW_SECONDS_WATCHED

        # try saving the new VideoLog: this is where the collision will happen, hopefully leading to a merge
        videolog.save()

        # get a new reference to the existing VideoLog
        videolog2 = VideoLog.objects.get(id=self.original_videolog.id)

        # make sure the VideoLog has been properly merged
        self.assertEqual(videolog.points, max(self.ORIGINAL_POINTS, self.NEW_POINTS), "The VideoLog's points were not properly merged.")
        self.assertEqual(videolog.total_seconds_watched, max(self.ORIGINAL_ATTEMPTS, self.NEW_SECONDS_WATCHED), "The VideoLog's total seconds watched have already changed.")
