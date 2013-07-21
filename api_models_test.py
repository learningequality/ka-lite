import unittest
from api_models import *

class ApiCallVideoTest(unittest.TestCase):

	def setUp(self):
		self.video_object = Video.get_video("adding-subtracting-negative-numbers")
	
	#@unittest.skip("Skiping get video test...")
	def test_get_video(self):
		self.assertEqual("adding-subtracting-negative-numbers", self.video_object.readable_id)


class ApiCallExerciseTest(unittest.TestCase):

	def setUp(self):
		self.exercises_list_object = Exercise.get_exercises()
		self.exercise_object = Exercise.get_exercise("logarithms_1")
	
	#@unittest.skip("Skiping get exercises test...")
	def test_get_exercises(self):
		if not self.exercises_list_object:
			self.assertEqual(self.exercises_list_object, [])
		else:
			for obj in self.exercises_list_object:
				self.assertIsInstance(obj, Exercice)
	
	#@unittest.skip("Skiping get exercise test...")
	def test_get_exercise(self):
		self.assertEqual("logarithms_1", self.exercise_object.name)


class ApiCallTopicTest(unittest.TestCase):

	def setUp(self):
		self.topic_tree_object = Topic.get_tree()
		self.topic_subtree_object = Topic.get_tree("addition-subtraction")
		self.topic_exercises_list_object = Topic.get_topic_exercises("addition-subtraction")
		self.topic_videos_list_object = Topic.get_topic_videos("addition-subtraction")
	
	#@unittest.skip("Skiping get tree test...")	
	def test_get_tree(self):
		self.assertIsInstance(self.topic_tree_object, Topic)
	
	#@unittest.skip("Skiping get subtree...")
	def test_get_subtree(self):
		self.assertEqual("addition-subtraction", self.topic_subtree_object.slug)

	#@unittest.skip("Skiping get topic exercises test...")
	def test_get_topic_exercises(self):
		if not self.topic_exercises_list_object:
			self.assertEqual(self.topic_exercises_list_object, [])
		else:
			for obj in self.topic_exercises_list_object:
				self.assertIsInstance(obj, Exercise)	

	#@unittest.skip("Skiping get topic videos test...")
	def test_get_topic_videos(self):
		if not self.topic_videos_list_object:
			self.assertEqual(self.topic_videos_list_object, [])
		else:
			for obj in self.topic_videos_list_object:
				self.assertIsInstance(obj, Video)


class ApiCallUserTest(unittest.TestCase):

	def setUp(self):
		self.user_get_user_object = User.get_user()

	@unittest.skip("Skiping get user test...")
	def test_get_user(self):
		self.assertIsInstance(self.user_get_user_object, User)


if __name__ == '__main__':
    unittest.main()
		
