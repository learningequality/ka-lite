import unittest
from api_models import *

class ApiCallVideoTest(unittest.TestCase):

	def setUp(self):
		self.video_object = Video.get_video("adding-subtracting-negative-numbers")
	@unittest.skip("")
	def test_get_video(self):
		self.assertEqual("adding-subtracting-negative-numbers", self.video_object.readable_id)


class ApiCallExerciseTest(unittest.TestCase):

	def setUp(self):
		self.exercises_list_object = Exercise.get_exercises()
		self.exercise_object = Exercise.get_exercise("logarithms_1")
	@unittest.skip("")
	def test_get_exercises(self):
		if not self.exercises_list_object:
			self.assertIsInstance(self.exercises_list_object, List)
		else:
			for obj in self.exercises_list_object:
				self.assertIsInstance(obj, Exercice)
	#@unittest.skip("")
	def test_get_exercise(self):
		self.assertEqual("logarithms_1", self.exercise_object.name)


class ApiCallTopicTest(unittest.TestCase):

	def setUp(self):
		self.topic_tree_object = Topic.get_tree()
		self.topic_subtree_object = Topic.get_tree("addition-subtraction")
		self.topic_exercises_object = Topic.get_topic_exercises("addition-subtraction")
		self.topic_videos_object = Topic.get_topic_videos("addition-subtraction")
	@unittest.skip("")	
	def test_get_tree(self):
		self.assertIsInstance(self.topic_tree_object, Topic)
	@unittest.skip("")
	def test_get_subtree(self):
		self.assertEqual("addition-subtraction", self.topic_subtree_object.slug)

	#def test_get_topic_exercises(self):


if __name__ == '__main__':
    unittest.main()
		
