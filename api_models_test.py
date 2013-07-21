import unittest
from api_models import *

class ApiCallExerciseTest(unittest.TestCase):

	def setUp(self):
		self.exercises_list_object = Exercise.get_exercises()
		self.exercise_object = Exercise.get_exercise("logarithms_1")
	
	def test_get_exercises(self):
		if not self.exercises_list_object:
			self.assertListEqual(self.exercises_list_object, [])
		else:
			for obj in self.exercises_list_object:
				self.assertIsInstance(obj, Exercise)

	def test_get_exercise(self):
		self.assertEqual("logarithms_1", self.exercise_object.name)


class ApiCallBadgeTest(unittest.TestCase):

	def setUp(self):
		self.badges_list_object = Badge.get_badges()
		self.badges_category_object = Badge.get_category(1)
		self.badges_category_list_object = Badge.get_category()

	def test_get_badges(self):
		if not self.badges_list_object:
			self.assertListEqual(self.badges_list_object, [])
		else:
			for obj in self.badges_list_object:
				self.assertIsInstance(obj, Badge)

	def test_get_category(self):
		self.assertEqual(self.badges_category_object.category, 1)

	def test_get_category_list(self):
		if not self.badges_category_list_object:
			self.assertListEqual(self.badges_category_list_object, [])
		else:
			for obj in self.badges_category_list_object:
				self.assertIsInstance(obj, BadgeCategory)


class ApiCallUserTest(unittest.TestCase):

	def setUp(self):
		self.user_get_user_object = User.get_user()

	def test_get_user(self):
		self.assertIsInstance(self.user_get_user_object, User)


class ApiCallTopicTest(unittest.TestCase):

	def setUp(self):
		self.topic_tree_object = Topic.get_tree()
		self.topic_subtree_object = Topic.get_tree("addition-subtraction")
		self.topic_exercises_list_object = Topic.get_topic_exercises("addition-subtraction")
		self.topic_videos_list_object = Topic.get_topic_videos("addition-subtraction")
	
	def test_get_tree(self):
		self.assertIsInstance(self.topic_tree_object, Topic)
	
	def test_get_subtree(self):
		self.assertEqual("addition-subtraction", self.topic_subtree_object.slug)

	def test_get_topic_exercises(self):
		if not self.topic_exercises_list_object:
			self.assertListEqual(self.topic_exercises_list_object, [])
		else:
			for obj in self.topic_exercises_list_object:
				self.assertIsInstance(obj, Exercise)	

	def test_get_topic_videos(self):
		if not self.topic_videos_list_object:
			self.assertListEqual(self.topic_videos_list_object, [])
		else:
			for obj in self.topic_videos_list_object:
				self.assertIsInstance(obj, Video)


class ApiCallVideoTest(unittest.TestCase):

	def setUp(self):
		self.video_object = Video.get_video("adding-subtracting-negative-numbers")
	
	def test_get_video(self):
		self.assertEqual("adding-subtracting-negative-numbers", self.video_object.readable_id)



def prepare_suites_from_test_cases(case_class_list):
	test_suites = []
	for cls in case_class_list:
		test_suites.append(unittest.TestLoader().loadTestsFromTestCase(cls))
	return test_suites


# test_cases contain the classes that will be tested. 
test_cases = [

	#ApiCallExerciseTest,
	#ApiCallBadgeTest,
	#ApiCallUserTest,
	#ApiCallTopicTest,
	#ApiCallVideoTest,

]


all_tests = unittest.TestSuite(prepare_suites_from_test_cases(test_cases))

unittest.TextTestRunner(verbosity=2).run(all_tests)
		
