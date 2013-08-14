from main import topicdata

def get_exercise_paths():
	"""This function retrieves all the exercise paths.
	"""
	exercises = topicdata.NODE_CACHE["Exercise"].values()
	return [exercise["paths"][0] for exercise in exercises if len(exercise.get("paths", [])) > 0]