import json

from django.test import TestCase
from django.utils import unittest

from main.models import VideoLog, ExerciseLog
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

        # create an initial ExerciseLog instance so we have something to collide with later
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
        data = json.dumps({
            "exercise_id": self.EXERCISE_ID2,
            "streak_progress": self.NEW_STREAK_PROGRESS_LARGER,
            "points": self.NEW_POINTS_LARGER,
            "correct": True,
        })
        result = c.post("/api/save_exercise_log", data=data, content_type="application/json")
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
        data = json.dumps({
            "exercise_id": self.EXERCISE_ID,
            "streak_progress": self.NEW_STREAK_PROGRESS_LARGER,
            "points": self.NEW_POINTS_LARGER,
            "correct": True,
        })
        result = c.post("/api/save_exercise_log", data=data, content_type="application/json")
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the exercise log." % result.status_code)
        
        # get a reference to the updated ExerciseLog
        exerciselog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_ID, user__username=self.USERNAME)
        
        # make sure the ExerciseLog was properly updated
        self.assertEqual(exerciselog.points, self.NEW_POINTS_LARGER, "The ExerciseLog's points were not saved correctly.")
        self.assertEqual(exerciselog.streak_progress, self.NEW_STREAK_PROGRESS_LARGER, "The ExerciseLog's streak progress was not saved correctly.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS + 1, "The ExerciseLog did not have the correct number of attempts.")

        # save a new record onto the exercise log, with an incorrect answer (decreasing the points and streak)
        data = json.dumps({
            "exercise_id": self.EXERCISE_ID,
            "streak_progress": self.NEW_STREAK_PROGRESS_SMALLER,
            "points": self.NEW_POINTS_SMALLER,
            "correct": False,
        })
        result = c.post("/api/save_exercise_log", data=data, content_type="application/json")
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the exercise log." % result.status_code)
        
        # get a reference to the updated ExerciseLog
        exerciselog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_ID, user__username=self.USERNAME)
        
        # make sure the ExerciseLog was properly updated
        self.assertEqual(exerciselog.points, self.NEW_POINTS_SMALLER, "The ExerciseLog's points were not saved correctly.")
        self.assertEqual(exerciselog.streak_progress, self.NEW_STREAK_PROGRESS_SMALLER, "The ExerciseLog's streak progress was not saved correctly.")
        self.assertEqual(exerciselog.attempts, self.ORIGINAL_ATTEMPTS + 2, "The ExerciseLog did not have the correct number of attempts.")        

