'''
This module contains all tests for the functions invoked to
get the "Next" recommendations.
'''

import unittest
from kalite.topic_tools.content_recommendation import *

class TestNextMethods(unittest.TestCase):

	def setUp(self):
		'''Performed before every test'''
		self.user_with_no_activity = 1	#a brand new user
		self.user_with_activity = 2		#a user with valid rows in Facility+ExerciseLogs

	def tearDown(self):
		'''Performed after each test'''
		self.user_with_activity = None
		self.user_with_no_activity = None

	def test_next_overall(self):
		'''get_next_recommendations()'''
		pass

	def test_group_recommendations(self):
		'''get_group_recommendations()'''
		pass

	def test_struggling(self):
		'''get_struggling_exercises()'''
		pass

	def test_exercise_prereqs(self):
		'''get_exercise_prereqs()'''
		pass


#runs tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestNextMethods)
unittest.TextTestRunner(verbosity=2).run(suite)