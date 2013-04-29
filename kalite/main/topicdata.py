import json
from config.models import Settings

TOPICS          = json.loads(open(Settings.get("DATA_PATH") + "topics.json").read())
NODE_CACHE      = json.loads(open(Settings.get("DATA_PATH") + "nodecache.json").read())
EXERCISE_TOPICS = json.loads(open(Settings.get("DATA_PATH") + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(Settings.get("DATA_PATH") + "languages.json").read())
LANGUAGE_LIST   = json.loads(open(Settings.get("DATA_PATH") + "listedlanguages.json").read())