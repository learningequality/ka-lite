'''
This module contains all tests for the functions implemented and used
in multiple content recommendation functions.
'''

import unittest
from kalite.topic_tools.content_recommendation import *

class TestHelperMethods(unittest.TestCase):

	def setUp(self):
		'''Performed before every test'''
		self.user_with_no_activity = 1	#a brand new user
		self.user_with_activity = 2		#a user with valid rows in Facility+ExerciseLogs

	def tearDown(self):
		'''Performed after each test'''
		self.user_with_activity = None
		self.user_with_no_activity = None

	def test_exercise_parents_lookup_table(self):
		'''get_exercise_parents_lookup_table()'''
		pass

	def test_exercises_from_topics(self):
		'''get_exercises_from_topics()'''
		pass

	def test_most_recent_exercises(self):
		'''get_most_recent_exercises()'''
		pass



#runs tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestHelperMethods)
unittest.TextTestRunner(verbosity=2).run(suite)
