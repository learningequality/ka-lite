'''
This module contains all tests for the functions invoked to
get the "Explore" recommendations.
'''

import unittest
from kalite.topic_tools.content_recommendation import *

class TestExploreMethods(unittest.TestCase):

	def setUp(self):
		'''Performed before every test'''
		pass

	def tearDown(self):
		'''Performed after each test'''
		pass 

	def test_explore_overall(self):
		'''get_explore_recommendations()'''
		pass

	def test_subtopic_data(self):
		'''get_subtopic_data()'''
		pass




#runs tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestExploreMethods)
unittest.TextTestRunner(verbosity=2).run(suite)