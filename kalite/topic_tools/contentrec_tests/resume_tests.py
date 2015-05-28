'''
This module contains all tests for the functions invoked to
get the "Resume" recommendations.
'''

import unittest
from kalite.topic_tools.content_recommendation import *

class TestResumeMethods(unittest.TestCase):

	def setUp(self):
		'''Performed before every test'''

		#a brand new user - need to refactor to perhaps make a new user
		self.user_with_no_activity = FacilityUser.objects.filter(first_name='Allen')[0] 

		#a user with valid rows in Facility+ExerciseLogs
		self.user_with_activity = ExerciseLog.objects.all()[0].user														

	def tearDown(self):
		'''Performed after each test'''

		self.user_with_activity = None
		self.user_with_no_activity = None

	def test_resume_overall(self):
		'''get_resume_recommendations()'''
		
		#manually grab the most recent exercise by the user
		exercises = ExerciseLog.objects.filter(user=self.user_with_activity)
		most_recent = sorted(exercises, key=lambda ex:ex.completion_timestamp, reverse=True)[:1]
		print most_recent

		#assertions
		self.assertEqual(get_resume_recommendations(self.user_with_no_activity, None), [], "New user")
		self.assertEqual(get_resume_recommendations(self.user_with_activity, {"language":"en-us"}), most_recent, "User with Exs")

		

	def test_get_most_recent_incomplete_item(self):
		'''get_most_recent_incomplete_item()'''

		exercises = ExerciseLog.objects.filter(user=self.user_with_activity)
		most_recent = sorted(exercises, key=lambda ex:ex.completion_timestamp, reverse=True)
		
		most_recent_incomplete_exercise = None
		for ex in most_recent:
			if not ex.complete:
				most_recent_incomplete_exercise = ex

		if most_recent_incomplete_exercise:
			self.assertEqual([most_recent_incomplete_exercise], get_most_recent_incomplete_item)




#runs tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestResumeMethods)
unittest.TextTestRunner(verbosity=2).run(suite)
