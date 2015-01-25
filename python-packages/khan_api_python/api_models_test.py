import unittest
from api_models import *

class ApiCallExerciseTest(unittest.TestCase):
	"""Performs an API call to fetch exercises and verifies the result.

	Attributes:
		exercises_list_object: A list of Exercise objects.
		exercise_object: An Exercise object that was specifically requested.
	"""

	def setUp(self):
		"""Prepares the objects that will be tested."""
		self.exercises_list_object = Khan().get_exercises()
		self.exercise_object = Khan().get_exercise("logarithms_1")
	
	def test_get_exercises(self):
		"""Tests if the result is an empty list or if it is a list of Exercise objects."""
		if not self.exercises_list_object:
			self.assertListEqual(self.exercises_list_object, [])
		else:
			for obj in self.exercises_list_object:
				self.assertIsInstance(obj, Exercise)

	def test_get_exercise(self):
		"""Tests if the result object contains the requested Exercise ID."""
		self.assertEqual("logarithms_1", self.exercise_object.name)

	def test_get_exercise_related_videos(self):
		"""Tests if the result is and empty list or if it is a list of Video objects."""
		if not self.exercise_object.related_videos:
			self.assertListEqual(self.exercise_object.related_videos, [])
		else:
			for obj in self.exercise_object.related_videos:
				self.assertIsInstance(obj, Video)

	def test_get_exercise_followup_exercises(self):
		"""Tests if the result is and empty list or if it is a list of Exercise objects."""
		if not self.exercise_object.followup_exercises:
			self.assertListEqual(self.exercise_object.followup_exercises, [])
		else:
			for obj in self.exercise_object.followup_exercises:
				self.assertIsInstance(obj, Exercise)


class ApiCallBadgeTest(unittest.TestCase):
	"""Performs an API call to fetch badges and verifies the result.

	Attributes:
		badges_list_object: A list of Badge objects.
		badges_category_object: A BadgeCategory object that was specifically requested.
		badges_category_list_object: A list of BadgeCategory objects.
	"""

	def setUp(self):
		"""Prepares the objects that will be tested."""
		self.badges_list_object = Khan().get_badges()
		self.badges_category_object = Khan().get_badge_category(1)
		self.badges_category_list_object = Khan().get_badge_category()

	def test_get_badges(self):
		"""Tests if the result is an empty list or if it is a list of Bagde objects."""
		if not self.badges_list_object:
			self.assertListEqual(self.badges_list_object, [])
		else:
			for obj in self.badges_list_object:
				self.assertIsInstance(obj, Badge)

	def test_get_category(self):
		"""Tests if the result object contains the requested Badge category."""
		self.assertEqual(self.badges_category_object.category, 1)

	def test_get_category_list(self):
		"""Tests if the result is an empty list or if it is a list of BadgeCategory objects."""
		if not self.badges_category_list_object:
			self.assertListEqual(self.badges_category_list_object, [])
		else:
			for obj in self.badges_category_list_object:
				self.assertIsInstance(obj, BadgeCategory)



class ApiCallUserTest(unittest.TestCase):
	"""Performs an API call to fetch user data and verifies the result.

	This test will require login in Khan Academy.

	Attributes:
		user_object: An User object that is created after the user login.
		badges_object: A Badge object that cointains UserBadge objects if the user is logged in.
	"""

	def setUp(self):
		"""Prepares the objects that will be tested."""
		self.user_object = Khan().get_user()
		self.badges_object = Khan().get_badges()

	def test_get_user(self):
		"""Tests if the result is an instance of User. The object is created if the result of the API call is a success."""
		self.assertIsInstance(self.user_object, User)

	def test_get_user_videos(self):
		"""Tests if the result is an empty list or if it is a list of UserVideo objects.
		   For each UserVideo object check if log contains VideoLog objects.
		"""
		if not self.user_object.videos:
			self.assertListEqual(self.user_object.videos, [])
		else:
			for obj in self.user_object.videos:
				self.assertIsInstance(obj, UserVideo)
				if not obj.log:
					self.assertListEqual(obj.log, [])
				else:
					for l_obj in obj.log:
						self.assertIsInstance(l_obj, VideoLog)

	def test_get_user_exercises(self):
		"""Tests if the result is an empty list or if it is a list of UserExercise objects.
		   For each UserExercise object, checks if log attribute only contains ProblemLog objects
		   and if followup_exercises attribute only contains UserExercise objects.
		"""
		if not self.user_object.exercises:
			self.assertListEqual(self.user_object.exercises, [])
		else:
			for obj in self.user_object.exercises:
				self.assertIsInstance(obj, UserExercise)
				if not obj.log:
					self.assertListEqual(obj.log, [])
				else:
					for l_obj in obj.log:
						self.assertIsInstance(l_obj, ProblemLog)
				if not obj.followup_exercises:
					self.assertListEqual(obj.followup_exercises, [])
				else:
					for f_obj in obj.followup_exercises:
						self.assertIsInstance(f_obj, UserExercise)

	def test_get_user_badges(self):
		"""Tests if the result is an empty list or if it is a list of Badge objects. 
		   Then for each Badge, if it contains the user_badges key, it must be an instance of User Badges.
		"""
		if not self.badges_object:
			self.assertListEqual(self.badges_object, [])
		else:
			for obj in self.badges_object:
				if not obj.__contains__("user_badges"):
					continue
				else:
					for u_obj in obj.user_badges:
						self.assertIsInstance(u_obj, UserBadge)


class ApiCallTopicTest(unittest.TestCase):
	"""Performs an API call to fetch Topic data and verifies the result.

	Attributes:
		topic_tree_object: A Topic object that represents the entire Topic tree.
		topic_subtree_object: A Topic object that was specifically requested. It represents a subtree. 
	"""

	def setUp(self):
		"""Prepares the objects that will be tested."""
		self.topic_tree_object = Khan().get_topic_tree()
		self.topic_subtree_object = Khan().get_topic_tree("addition-subtraction")
		self.topic_exercises_list_object = Khan().get_topic_exercises("addition-subtraction")
		self.topic_videos_list_object = Khan().get_topic_videos("addition-subtraction")
	
	def test_get_tree(self):
		"""Tests if the result is an instance of Topic."""
		self.assertIsInstance(self.topic_tree_object, Topic)
	
	def test_get_subtree(self):
		"""Tests if the result object contains the requested topic slug."""
		self.assertEqual("addition-subtraction", self.topic_subtree_object.slug)

	def test_get_topic_exercises(self):
		"""Tests if the result is an empty list or if it is a list of Exercise objects."""
		if not self.topic_exercises_list_object:
			self.assertListEqual(self.topic_exercises_list_object, [])
		else:
			for obj in self.topic_exercises_list_object:
				self.assertIsInstance(obj, Exercise)	

	def test_get_topic_videos(self):
		"""Tests if the result is an emtpy list or if it is a list of Video objects."""
		if not self.topic_videos_list_object:
			self.assertListEqual(self.topic_videos_list_object, [])
		else:
			for obj in self.topic_videos_list_object:
				self.assertIsInstance(obj, Video)



class ApiCallVideoTest(unittest.TestCase):
	"""Performs an API call to fetch video data and verifies the result.

	Attributes:
		video_object: A Video object that was specifically requested.
	"""

	def setUp(self):
		"""Prepares the objects that will be tested."""
		self.video_object = Khan().get_video("adding-subtracting-negative-numbers")
	
	def test_get_video(self):
		"""Tests if the result object contains the requested video readable id."""
		self.assertEqual("adding-subtracting-negative-numbers", self.video_object.readable_id)



def prepare_suites_from_test_cases(case_class_list):
	"""
	This function prepares a list of suites to be tested.
	"""
	test_suites = []
	for cls in case_class_list:
		test_suites.append(unittest.TestLoader().loadTestsFromTestCase(cls))
	return test_suites



# "test_cases" contains the classes that will be tested. 
# Add or remove test cases as needed.
test_cases = [

	ApiCallExerciseTest,
	ApiCallBadgeTest,
	ApiCallUserTest,
	ApiCallTopicTest,
	ApiCallVideoTest,

]

# Prepares a set of suites.
all_tests = unittest.TestSuite(prepare_suites_from_test_cases(test_cases))

# Runs all tests on suites passed as an argument.
unittest.TextTestRunner(verbosity=2).run(all_tests)
		
