import json
from settings import DATA_PATH


TOPICS = json.loads(open(DATA_PATH + "topics.json").read())
NODE_CACHE = json.loads(open(DATA_PATH + "nodecache.json").read())
EXERCISE_TOPICS = json.loads(open(DATA_PATH + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(DATA_PATH + "languages.json").read())
LANGUAGE_LIST = json.loads(open(DATA_PATH + "listedlanguages.json").read())

def get_videos(topic): return filter(lambda node: node["kind"] == "Video", topic["children"])
def get_exercises(topic): return filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])
def get_live_topics(topic): return filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])
