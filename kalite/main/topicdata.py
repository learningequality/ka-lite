import json
import settings

TOPICS = json.loads(open(settings.DATA_PATH + "topics.json").read())
NODE_CACHE = json.loads(open(settings.DATA_PATH + "nodecache.json").read())
EXERCISE_TOPICS = json.loads(open(settings.DATA_PATH + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(settings.DATA_PATH + "languages.json").read())
LANGUAGE_LIST = json.loads(open(settings.DATA_PATH + "listedlanguages.json").read())

# Any None value will break translation code.  
#   Rather than check, just guarantee that no values are none!
for v in NODE_CACHE['Video'].values():
    if v['description'] is None:
        v['description'] = ""
