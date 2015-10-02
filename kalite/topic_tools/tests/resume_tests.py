'''
This module contains all tests for the functions invoked to
get the "Resume" recommendations.
'''
import datetime

from kalite.topic_tools.content_recommendation import get_most_recent_incomplete_item
from kalite.testing.base import KALiteTestCase
from kalite.facility.models import Facility, FacilityUser
from kalite.main.models import ExerciseLog

class TestResumeMethods(KALiteTestCase):

	ORIGINAL_POINTS = 37
	ORIGINAL_ATTEMPTS = 3
	ORIGINAL_STREAK_PROGRESS = 20
	NEW_POINTS_LARGER = 22
	NEW_ATTEMPTS = 5
	NEW_STREAK_PROGRESS_LARGER = 10
	NEW_POINTS_SMALLER = 0
	NEW_STREAK_PROGRESS_SMALLER = 0
	EXERCISE_ID = "number_line"
	EXERCISE_ID2 = "radius_diameter_and_circumference"
	USERNAME1 = "test_user_resume1"
	USERNAME2 = "test_user_resume2"
	PASSWORD = "dummies"
	FACILITY = "Test Facility Resume"
	TIMESTAMP_LATER = datetime.datetime(2014, 11, 17, 20, 51, 2, 342662)
	TIMESTAMP_EARLY = datetime.datetime(2014, 10, 8, 15, 59, 59, 370290)

	def setUp(self):
		'''Performed before every test'''

		#a brand new user 
		self.facility = Facility(name=self.FACILITY)
		self.facility.save()

		self.user_with_no_activity = FacilityUser(username=self.USERNAME1, facility=self.facility)
		self.user_with_no_activity.set_password(self.PASSWORD)
		self.user_with_no_activity.save()

		#a user with valid exercises
		self.user_with_activity = FacilityUser(username=self.USERNAME2, facility=self.facility)
		self.user_with_activity.set_password(self.PASSWORD)		
		self.user_with_activity.save()							

		#add some exercises for second user (both incomplete)
		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID, user = self.user_with_activity, complete=False)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_POINTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.save()

		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID2, user = self.user_with_activity, complete=False)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_POINTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.save()		

	def test_get_most_recent_incomplete_item(self):
		'''get_most_recent_incomplete_item()'''

		#test user with activity first
		expected = {
			"id": unicode(self.EXERCISE_ID2, 'utf-8'),
			"timestamp": self.TIMESTAMP_LATER,
			"kind": "Exercise"
		}
		actual = get_most_recent_incomplete_item(self.user_with_activity)
		self.assertEqual(expected, actual)


		#new user just created (no activity logged)
		self.assertIsNone(get_most_recent_incomplete_item(user=self.user_with_no_activity))
