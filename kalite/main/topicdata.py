import json
import settings

TOPICS = json.loads(open(settings.DATA_PATH + "topics.json").read())
NODE_CACHE = json.loads(open(settings.DATA_PATH + "nodecache.json").read())
EXERCISE_TOPICS = json.loads(open(settings.DATA_PATH + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(settings.DATA_PATH + "languages.json").read())
LANGUAGE_LIST = json.loads(open(settings.DATA_PATH + "listedlanguages.json").read())
ID2SLUG_MAP = json.loads(open(settings.DATA_PATH + "youtube_to_slug_map.json").read())