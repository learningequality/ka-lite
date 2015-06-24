'''
This module contains all tests for the functions invoked to
get the "Explore" recommendations.
'''

from django.test.client import RequestFactory
from kalite.topic_tools.content_recommendation import *
from kalite.testing.base import KALiteTestCase

class TestExploreMethods(KALiteTestCase):

	ORIGINAL_POINTS = 37
	ORIGINAL_ATTEMPTS = 3
	ORIGINAL_STREAK_PROGRESS = 20
	NEW_POINTS_LARGER = 22
	NEW_ATTEMPTS = 5
	NEW_STREAK_PROGRESS_LARGER = 10
	NEW_POINTS_SMALLER = 0
	NEW_STREAK_PROGRESS_SMALLER = 0
	EXERCISE_ID = "number_line"
	USERNAME1 = "test_user_explore_1"
	PASSWORD = "dummies"
	FACILITY = "Test Facility Explore"
	TIMESTAMP = datetime.datetime(2014, 11, 17, 20, 51, 2, 342662)

	def setUp(self):
		'''Performed before every test'''

		# create a facility and user that can be referred to in models across tests
		self.facility = Facility(name=self.FACILITY)
		self.facility.save()

		self.user1 = FacilityUser(username=self.USERNAME1, facility=self.facility)
		self.user1.set_password(self.PASSWORD)
		self.user1.save()

		#add one exercise
		self.original_exerciselog = ExerciseLog(exercise_id=self.EXERCISE_ID, user=self.user1)
		self.original_exerciselog.points = self.ORIGINAL_POINTS
		self.original_exerciselog.attempts = self.ORIGINAL_ATTEMPTS
		self.original_exerciselog.streak_progress = self.ORIGINAL_STREAK_PROGRESS
		self.original_exerciselog.latest_activity_timestamp = self.TIMESTAMP
		self.original_exerciselog.completion_timestamp = self.TIMESTAMP
		self.original_exerciselog.save()

		#create a request factory for later instantiation of request
		self.factory = RequestFactory() 

	def test_explore_overall(self):
		'''get_explore_recommendations()'''

		#create a request object and set the language attribute
		request = self.factory.get('/content_recommender?explore=true')
		request.language = settings.LANGUAGE_CODE
		
		expected=[{'interest_topic': {'icon_src': '', 'topic_page_url': '/math/arithmetic', 'kind': 'Topic', 'contains': ['Topic', 'Video', 'Exercise'], 'hide': False, 'description': 'So you\'re ready to have some arithmetic fun? You\'ve come to the right spot! It\'s the first "official" math topic and chalked full of fun exercises and great videos which help you start your journey towards math mastery. We\'ll cover the big ones: addition, subtraction, multiplication, and division, of course. But we don\'t stop there. We\'ll get into negative numbers, absolute value, decimals, and fractions, too. Learning math should be fun, and we plan on having some with you. Ready to get started? ', 'parent': 'math', 'node_slug': 'arithmetic', 'render_type': 'Subject', 'children': ['addition-subtraction', 'multiplication-division', 'absolute-value', 'decimals', 'fractions', 'telling-time-topic'], 'available': True, 'path': 'khan/math/arithmetic/', 'id': 'arithmetic', 'title': 'Arithmetic', 'extended_slug': 'math/arithmetic', 'slug': 'arithmetic', 'in_knowledge_map': False}, 'suggested_topic': {'icon_src': '', 'topic_page_url': '/math/pre-algebra', 'kind': 'Topic', 'contains': ['Topic', 'Video', 'Exercise'], 'hide': False, 'description': "No way, this isn't your run of the mill arithmetic. This is Pre-algebra. You're about to play with the professionals. Think of pre-algebra as a runway. You're the airplane and algebra is your sunny vacation destination. Without the runway you're not going anywhere. Seriously, the foundation for all higher mathematics is laid with many of the concepts that we will introduce to you here: negative numbers, absolute value, factors, multiples, decimals, and fractions to name a few. So buckle up and move your seat into the upright position. We're about to take off!", 'parent': 'math', 'node_slug': 'pre-algebra', 'render_type': 'Subject', 'children': ['negatives-absolute-value-pre-alg', 'factors-multiples', 'decimals-pre-alg', 'fractions-pre-alg', 'rates-and-ratios', 'applying-math-reasoning-topic', 'exponents-radicals', 'order-of-operations', 'measurement'], 'available': True, 'path': 'khan/math/pre-algebra/', 'id': 'pre-algebra', 'title': 'Pre-algebra', 'extended_slug': 'math/pre-algebra', 'slug': 'pre-algebra', 'in_knowledge_map': False}}]
		actual = get_explore_recommendations(self.user1, request)
		self.assertEqual(expected, actual)
