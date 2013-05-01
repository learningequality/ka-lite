import json
import settings

TOPICS = json.loads(open(settings.DATA_PATH + "topics.json").read())
NODE_CACHE = json.loads(open(settings.DATA_PATH + "nodecache.json").read())
EXERCISE_TOPICS = json.loads(open(settings.DATA_PATH + "maplayout_data.json").read())
LANGUAGE_LOOKUP = json.loads(open(settings.DATA_PATH + "languages.json").read())
LANGUAGE_LIST = json.loads(open(settings.DATA_PATH + "listedlanguages.json").read())

def get_videos(topic): 
    """Given a topic node, returns all video node children"""
    return filter(lambda node: node["kind"] == "Video", topic["children"])
    
def get_exercises(topic): 
    """Given a topic node, returns all exercise node children"""
    return filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])

def get_live_topics(topic): 
    """Given a topic node, returns all children that are not hidden and contain at least one video"""
    return filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])
