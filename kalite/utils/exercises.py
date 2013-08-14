from main import topicdata

def get_exercise_paths():
	"""This function retrieves all the exercise urls.
	"""
	exercises = topicdata.NODE_CACHE["Exercise"].values()
	return [exercise["paths"][0] for exercise in exercises if len(exercise.get("paths", [])) > 0]
	#exercises_urls = []
	#for item in topicdata.NODE_CACHE.get("Exercise").items():
	#	for obj in item:
	#		if type(obj) is dict and obj.has_key("paths"):
	#			exercises_urls.append(obj.get('paths')[0])

	#return exercises_urls