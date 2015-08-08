'''
This module contains all tests for the functions implemented and used
in multiple content recommendation functions.
'''
import datetime

from kalite.topic_tools.content_recommendation import get_exercises_from_topics, get_most_recent_exercises
from kalite.testing.base import KALiteTestCase
from kalite.facility.models import Facility, FacilityUser
from kalite.main.models import ExerciseLog

class TestHelperMethods(KALiteTestCase):

	TOPIC_TO_TEST = 'decimal-to-fraction-pre-alg' #actually a subtopic, but is still valid
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
	USERNAME1 = "test_user_helper1" 
	PASSWORD = "dummies"
	FACILITY = "Test Facility Next Steps"
	TIMESTAMP_LATER = datetime.datetime(2014, 11, 17, 20, 51, 2, 342662)
	TIMESTAMP_EARLY = datetime.datetime(2014, 10, 8, 15, 59, 59, 370290)

	def setUp(self):
		'''Performed before every test'''
		
		#user + facility
		self.facility = Facility(name=self.FACILITY)
		self.facility.save()

		self.user1 = FacilityUser(username=self.USERNAME1, facility=self.facility)
		self.user1.set_password(self.PASSWORD)
		self.user1.save()

		#insert some exercise activity
		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID, user = self.user1)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_POINTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.struggling = False
		self.original_exerciselog2.save()

		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID2, user = self.user1)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_POINTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.struggling = False
		self.original_exerciselog2.save()

	def tearDown(self):
		'''Performed after each test'''
		self.user_with_activity = None
		self.user_with_no_activity = None

	def test_exercises_from_topics(self):
		'''get_exercises_from_topics()'''

		expected = ['converting_fractions_to_decimals',
					'converting_decimals_to_fractions_1', 
					'converting_decimals_to_fractions_2']
		actual = get_exercises_from_topics([self.TOPIC_TO_TEST])

		self.assertEqual(expected, actual)

	def test_most_recent_exercises(self):
		'''get_most_recent_exercises()'''

		first = "radius_diameter_and_circumference"
		second = "number_line"
		expected = [unicode(first, 'utf-8'), unicode(second, 'utf-8')]
		actual = get_most_recent_exercises(self.user1)
	
		self.assertSequenceEqual(expected, actual)
