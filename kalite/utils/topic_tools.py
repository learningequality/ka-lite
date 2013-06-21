"""
"""
import glob
from functools import partial

import settings
from main import topicdata


def find_videos_by_youtube_id(youtube_id, node=topicdata.TOPICS):
    videos = []
    if node.get("youtube_id", "") == youtube_id:
        videos.append(node)
    for child in node.get("children", []):
        videos += find_videos_by_youtube_id(youtube_id, child)
    return videos

# find_video_by_youtube_id("NSSoMafbBqQ")

def get_all_youtube_ids(node=topicdata.TOPICS):
    if node.get("youtube_id", ""):
        return [node.get("youtube_id", "")]
    ids = []
    for child in node.get("children", []):
        ids += get_all_youtube_ids(child)
    return ids

def get_dups(threshold=2):
    ids = get_all_youtube_ids()
    return [id for id in set(ids) if ids.count(id) >= threshold]
    
def print_videos(youtube_id):
    print "Videos with YouTube ID '%s':" % youtube_id
    for node in find_videos_by_youtube_id(youtube_id):
        print " > ".join(node["path"].split("/")[1:-3] + [node["title"]])
        
def get_downloaded_youtube_ids():
    return [path.split("/")[-1].split(".")[0] for path in glob.glob("../../content/*.mp4")]
    
    

def get_topic_by_path(path):
    """Given a topic path, return the corresponding topic node in the topic hierarchy"""
    # Make sure the root fits
    root_node = topicdata.TOPICS
    if not path.startswith(root_node["path"]):
        return None
        
    # split into parts (remove trailing slash first)
    parts = path[len(root_node["path"]):-1].split("/")
    cur_node = root_node
    for part in parts:
        cur_node = filter(partial(lambda n,p: n["id"]==p, p=part), cur_node["children"])
        if cur_node:
            cur_node = cur_node[0]
        else:
            break;
            
    assert not cur_node or cur_node["path"] == path, "Either didn't find it, or found the right thing."

    return cur_node 


def get_all_leaves(leaf_type, topic_node=topicdata.TOPICS):
    leaves = []
    
    # base case
    if not "children" in topic_node:
        if topic_node['kind'] == leaf_type:
            leaves.append(topic_node)
    else:
        for child in topic_node["children"]:
            leaves += get_all_leaves(topic_node=child, leaf_type=leaf_type)
    
    return leaves
    
def get_topic_leaves(leaf_type, topic_id=None, path=None):
    """Given a topic (identified by topic_id or path), return all ancestor exercises"""
    assert (topic_id or path) and not (topic_id and path), "Specify topic_id or path, not both."
    
    if not path:
        topic_node = filter(partial(lambda node,name: node['id']==name, name=topic_id), topicdata.NODE_CACHE['Topic'].values())
        if not topic_node:
            return []
        path = topic_node[0]['path']

    # More efficient way
    topic_node = get_topic_by_path(path)
    exercises = get_all_leaves(topic_node=topic_node, leaf_type=leaf_type)

    # Brute force way
    #exercises = []
    #for ex in topicdata.NODE_CACHE['Exercise'].values():
    #    if ex['path'].startswith(path):
    #        exercises.append(ex)
    return exercises

def get_topic_exercises(*args, **kwargs):
    """Get all exercises for a particular set of topics"""
    return get_topic_leaves(leaf_type='Exercise', *args, **kwargs)
    
def get_topic_videos(*args, **kwargs):
    """Get all videos for a particular set of topics"""
    return get_topic_leaves(leaf_type='Video', *args, **kwargs)


def get_related_exercises(videos):
    """Given a set of videos, get all of their related exercises."""
    related_exercises = []
    for video in videos:
        if "related_exercise" in video:
            related_exercises.append(video['related_exercise'])
    return related_exercises

def get_related_videos(exercises, topics=None, possible_videos=None):
    """Given a set of exercises, get all of the videos that say they're related.
    
    possible_videos: list of videos to consider.
    topics: if not possible_videos, then get the possible videos from a list of topics.
    """
    related_videos = []

    if not possible_videos:
        possible_videos = []
        for topic in (topics or topicdata.NODE_CACHE['Topic'].values()):
            possible_videos += get_topic_videos(topic_id=topic['id'])
            
    # Get exercises from videos
    exercise_ids = [ex["id"] if "id" in ex else ex['name'] for ex in exercises]
    for video in videos:
        if "related_exercise" in video and video["related_exercise"]['id'] in exercise_ids:
            related_videos.append(video)
    return related_videos


def get_all_midlevel_topics():
    """Nobody knows what the true definition of these are, but this is the list of 
    exercise-related topics used in coach reports."""
    
    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    return topics
