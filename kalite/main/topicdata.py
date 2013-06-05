import json
import settings
import copy
from utils.topics import node_cache_from_topic

TOPICS = json.loads(open(settings.DATA_PATH + "topics.json").read())
NODE_CACHE = node_cache_from_topic(TOPICS)
EXERCISE_TOPICS = json.loads(open(settings.DATA_PATH + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(settings.DATA_PATH + "languages.json").read())
LANGUAGE_LIST = json.loads(open(settings.DATA_PATH + "listedlanguages.json").read())