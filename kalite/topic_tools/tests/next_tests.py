'''
This module contains all tests for the functions invoked to
get the "Next" recommendations.
'''

from kalite.topic_tools.content_recommendation import *
from kalite.facility.models import FacilityGroup
from kalite.testing.base import KALiteTestCase

class TestNextMethods(KALiteTestCase):

	ORIGINAL_POINTS = 37
	ORIGINAL_ATTEMPTS = 0
	ORIGINAL_STREAK_PROGRESS = 20
	NEW_POINTS_LARGER = 22
	NEW_ATTEMPTS = 5
	NEW_STREAK_PROGRESS_LARGER = 10
	NEW_POINTS_SMALLER = 0
	NEW_STREAK_PROGRESS_SMALLER = 0
	EXERCISE_ID = "number_line"
	EXERCISE_ID2 = "radius_diameter_and_circumference"
	EXERCISE_ID_STRUGGLE = "counting-out-1-20-objects"
	USERNAME1 = "test_user_next1"
	USERNAME2 = "test_user_next2"
	PASSWORD = "dummies"
	FACILITY = "Test Facility Next Steps"
	TIMESTAMP_LATER = datetime.datetime(2014, 11, 17, 20, 51, 2, 342662)
	TIMESTAMP_EARLY = datetime.datetime(2014, 10, 8, 15, 59, 59, 370290)
	TIMESTAMP_STRUGGLE = datetime.datetime(2014, 9, 17, 17, 43, 36, 405260)
	GROUP = 'Test Group Next Steps'

	def setUp(self):
		'''Performed before every test'''
	
		# create a facility and user that can be referred to in models across tests
		self.facility = Facility(name=self.FACILITY)
		self.facility.save()

		self.facilitygroup = FacilityGroup(name=self.GROUP, description="", facility=self.facility)
		self.facilitygroup.save()

		self.user1 = FacilityUser(username=self.USERNAME1, facility=self.facility, group=self.facilitygroup)
		self.user1.set_password(self.PASSWORD)
		self.user1.save()

		self.user2 = FacilityUser(username=self.USERNAME2, facility=self.facility, group=self.facilitygroup)
		self.user2.set_password(self.PASSWORD)
		self.user2.save()

		#user 1 - now add some mock data into exercise log
		self.original_exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user1)
		self.original_exerciselog.points = self.ORIGINAL_POINTS
		self.original_exerciselog.attempts = self.ORIGINAL_ATTEMPTS
		self.original_exerciselog.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog.latest_activity_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog.completion_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog.save()

		#user 2
		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID, user = self.user2, struggling=False)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_ATTEMPTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_EARLY
		self.original_exerciselog2.save()

		self.original_exerciselog2 = ExerciseLog(exercise_id=self.EXERCISE_ID2, user = self.user2, struggling=False)
		self.original_exerciselog2.points = self.ORIGINAL_POINTS
		self.original_exerciselog2.attempts = self.ORIGINAL_ATTEMPTS
		self.original_exerciselog2.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog2.latest_activity_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.completion_timestamp = self.TIMESTAMP_LATER
		self.original_exerciselog2.save()

		self.original_exerciselog3 = ExerciseLog(exercise_id=self.EXERCISE_ID_STRUGGLE, user = self.user2, struggling=True)
		self.original_exerciselog3.points = self.ORIGINAL_POINTS
		self.original_exerciselog3.attempts = self.ORIGINAL_POINTS #intentionally made larger to trigger struggling
		self.original_exerciselog3.streak_progress = 0
		self.original_exerciselog3.attempts = 100
		self.original_exerciselog3.latest_activity_timestamp = self.TIMESTAMP_STRUGGLE
		self.original_exerciselog3.completion_timestamp = self.TIMESTAMP_STRUGGLE
		self.original_exerciselog3.save()

		#set all other exercise's struggling param to false

	def test_group_recommendations(self):
		'''get_group_recommendations()'''

		user = FacilityUser.objects.filter(username=self.USERNAME1)[0]
		expected = ["radius_diameter_and_circumference"]
		actual = get_group_recommendations(user)

		self.assertEqual(expected, actual, "Group recommendations incorrect.")
		

	def test_struggling(self):
		'''get_struggling_exercises()'''

		expected = [unicode(self.EXERCISE_ID_STRUGGLE, 'utf-8')]
		actual = get_struggling_exercises(FacilityUser
			.objects
			.filter(username=self.USERNAME2)
			.order_by('-id')[0])

		self.assertSequenceEqual(expected, actual, "Struggling return incorrect.")

	def test_exercise_prereqs(self):
		'''get_exercise_prereqs()'''
		ex_id = 'equivalent_fractions'

		expected = ['visualizing-equivalent-fractions']
		actual = get_exercise_prereqs([ex_id])
		
		self.assertEqual(expected, actual, "Exercise Prereqs incorrect.")
