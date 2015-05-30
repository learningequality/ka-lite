'''
This module contains all tests for the functions invoked to
get the "Resume" recommendations.
'''

import unittest
from kalite.topic_tools.content_recommendation import *
#from kalite.testing.base import KALiteTestCase

class TestResumeMethods(unittest.TestCase):

	def setUp(self):
		'''Performed before every test'''

		#a brand new user 
		self.facility = Facility(name="Test Facility")
		self.facility.save()
		self.user_with_no_activity = FacilityUser(username="testuser", facility=self.facility)
		self.user_with_no_activity.set_password("dumber")
		self.user_with_no_activity.save()

		#a user with valid rows in Facility+ExerciseLogs, hence grabbing from ExerciseLog, random!
		self.user_with_activity = ExerciseLog.objects.order_by('?')[0].user												

	def tearDown(self):
		'''Performed after each test'''

		self.user_with_activity = None
		self.user_with_no_activity = None

	def test_resume_overall(self):
		'''get_resume_recommendations()'''
		
		#this is really just get_most_recent_incomplete item...


	def test_get_most_recent_incomplete_item(self):
		'''get_most_recent_incomplete_item()'''

		#test user with activity first
		exercises = ExerciseLog.objects.filter(user=self.user_with_activity, complete=False)
		videos = VideoLog.objects.filter(user=self.user_with_activity, complete=False)
		content = ContentLog.objects.filter(user=self.user_with_activity, complete=False)
		most_recent_exs = sorted(exercises, key=lambda ex:ex.latest_activity_timestamp, reverse=True)
		most_recent_vids = sorted(videos, key=lambda ex:ex.latest_activity_timestamp, reverse=True)
		most_recent_cont = sorted(content, key=lambda ex:ex.latest_activity_timestamp, reverse=True)
		
		expected = None
		top = []
		if most_recent_cont:
			top.append({
					"timestamp":most_recent_cont[0].latest_activity_timestamp or datetime.datetime.min,
					"id":most_recent_cont[0].content_id,
					"kind":"Content"
				})
		if most_recent_exs:
			top.append({
					"timestamp":most_recent_exs[0].latest_activity_timestamp or datetime.datetime.min,
					"id":most_recent_exs[0].exercise_id,
					"kind":"Exercise"
				})
		if most_recent_vids:
			top.append({
					"timestamp":most_recent_vids[0].latest_activity_timestamp or datetime.datetime.min,
					"id":most_recent_vids[0].video_id,
					"kind":"Video"
				})
		
		if top:
			expected = sorted(top, key=lambda ex: ex['timestamp'], reverse=True)[0]
		else:
			expected = []

		actual = get_most_recent_incomplete_item(self.user_with_activity)
		self.assertEqual(expected, actual)


		#new user just created (no activity logged)
		self.assertEqual(None, get_most_recent_incomplete_item(user=self.user_with_no_activity))



#runs tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestResumeMethods)
unittest.TextTestRunner(verbosity=2).run(suite)
