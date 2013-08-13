from main import topicdata

def get_exercises_urls():
	"""This function retrieves all the exercise urls.
	"""
	exercises_urls = []
	for item in topicdata.NODE_CACHE.get("Exercise").items():
		for obj in item:
			if type(obj) is dict and obj.has_key("paths"):
				exercises_urls.append(obj.get('paths')[0])

	return exercises_urls