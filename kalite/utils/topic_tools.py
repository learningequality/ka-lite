"""
Important constants and helpful functions
"""
import glob
import json
import os
from functools import partial

import settings
from settings import LOG as logging


kind_slugs = {
    "Video": "v/",
    "Exercise": "e/",
    "Topic": ""
}

topics_file = "topics.json"
node_cache_file = "nodecache.json"
map_layout_file = "maplayout_data.json"
video_remap_file = "youtube_to_slug_map.json"


# Globals that can be filled
TOPICS          = None
def get_topic_tree(force=False):
    global TOPICS, topics_file
    if TOPICS is None or force:
        TOPICS = json.loads(open(os.path.join(settings.DATA_PATH, topics_file)).read())
    return TOPICS


NODE_CACHE = None
def get_node_cache(node_type=None, force=False):
    global NODE_CACHE, node_cache_file
    if NODE_CACHE is None or force:
        NODE_CACHE      = json.loads(open(os.path.join(settings.DATA_PATH, node_cache_file)).read())
    if node_type is None:
        return NODE_CACHE
    else:
        return NODE_CACHE[node_type]


EXERCISE_TOPICS = None
def get_exercise_topics(force=False):
    global EXERCISE_TOPICS, map_layout_file
    if EXERCISE_TOPICS is None or force:
        EXERCISE_TOPICS = json.loads(open(os.path.join(settings.DATA_PATH, map_layout_file)).read())
    return EXERCISE_TOPICS


ID2SLUG_MAP = None
def get_id2slug_map(force=False):
    global ID2SLUG_MAP, video_remap_file
    if ID2SLUG_MAP is None or force:
        ID2SLUG_MAP     = json.loads(open(os.path.join(settings.DATA_PATH, video_remap_file)).read())
    return ID2SLUG_MAP



def get_videos(topic): 
    """Given a topic node, returns all video node children (non-recursively)"""
    return filter(lambda node: node["kind"] == "Video", topic["children"])


def get_exercises(topic): 
    """Given a topic node, returns all exercise node children (non-recursively)"""
    return filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])


def get_live_topics(topic): 
    """Given a topic node, returns all children that are not hidden and contain at least one video (non-recursively)"""
    return filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])


def find_videos_by_youtube_id(youtube_id, node=None):
    if node is None:
        node = get_topic_tree()
    videos = []
    if node.get("youtube_id", "") == youtube_id:
        videos.append(node)
    for child in node.get("children", []):
        videos += find_videos_by_youtube_id(youtube_id, child)
    return videos

# find_video_by_youtube_id("NSSoMafbBqQ")


def get_all_youtube_ids(node=None):
    if node is None:
        node = get_topic_tree()
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


def get_downloaded_youtube_ids(videos_path=settings.CONTENT_ROOT):
    return [path.split("/")[-1].split(".")[0] for path in glob.glob(videos_path + "*.mp4")]


def is_video_on_disk(youtube_id, videos_path=settings.CONTENT_ROOT):
    return os.path.isfile(videos_path + youtube_id + ".mp4")


_vid_last_updated = 0
_vid_last_count = 0


def video_counts_need_update(videos_path=settings.CONTENT_ROOT):
    global _vid_last_count
    global _vid_last_updated

    if not os.path.exists(videos_path):
        return False

    files = os.listdir(videos_path)

    vid_count = len(files)
    if vid_count:
        # TODO(bcipolli) implement this as a linear search, rather than sort-then-select.
        vid_last_updated = os.path.getmtime(sorted([(videos_path + f) for f in files], key=os.path.getmtime, reverse=True)[0])
    else:
        vid_last_updated = 0
    need_update = (vid_count != _vid_last_count) or (vid_last_updated != _vid_last_updated)

    _vid_last_count = vid_count
    _vid_last_updated = vid_last_updated

    return need_update


def get_video_counts(topic, videos_path, force=False):
    """ Uses the (json) topic tree to query the django database for which video files exist

    Returns the original topic dictionary, with two properties added to each NON-LEAF node:
      * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan Academy library)
      * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
    And the following property for leaf nodes:
      * on_disk

    Input Parameters:
    * videos_path: the path to video files
    """

    nvideos_local = 0
    nvideos_known = 0

    # Can't deal with leaves
    if not "children" in topic:
        raise Exception("should not be calling this function on leaves; it's inefficient!")

    # Only look for videos if there are more branches
    elif len(topic["children"]) == 0:
        logging.debug("no children: %s" % topic)

    elif len(topic["children"]) > 0:
        # RECURSIVE CALL:
        #  The children have children, let them figure things out themselves
        # $ASSUMPTION: if first child is a branch, THEY'RE ALL BRANCHES.
        #              if first child is a leaf, THEY'RE ALL LEAVES
        if "children" in topic["children"][0]:
            for child in topic["children"]:
                (child, _, _) = get_video_counts(topic=child, videos_path=videos_path)
                nvideos_local += child["nvideos_local"]
                nvideos_known += child["nvideos_known"]

        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = get_videos(topic)
            if len(videos) > 0:

                for video in videos:
                    # Mark all videos as not found
                    video["on_disk"] = is_video_on_disk(video["youtube_id"], videos_path)
                    nvideos_local += int(video["on_disk"])  # add 1 if video["on_disk"]
                nvideos_known = len(videos)

    topic["nvideos_local"] = nvideos_local
    topic["nvideos_known"] = nvideos_known
    return (topic, nvideos_local, nvideos_known)


def get_topic_by_path(path):
    """Given a topic path, return the corresponding topic node in the topic hierarchy"""
    # Make sure the root fits
    root_node = get_topic_tree()
    if not path.startswith(root_node["path"]):
        return None

    # split into parts (remove trailing slash first)
    parts = path[len(root_node["path"]):-1].split("/")
    cur_node = root_node
    for part in parts:
        cur_node = filter(partial(lambda n, p: n["slug"] == p, p=part), cur_node["children"])
        if cur_node:
            cur_node = cur_node[0]
        else:
            break

    assert not cur_node or cur_node["path"] == path, "Either didn't find it, or found the right thing."

    return cur_node


def get_all_leaves(topic_node=None, leaf_type=None):
    """
    Recurses the topic tree to return all leaves of type leaf_type, at all levels of the tree.

    If leaf_type is None, returns all child nodes of all types and levels.
    """
    if not topic_node:
        topic_node = get_topic_tree()
    leaves = []

    # base case
    if not "children" in topic_node:
        if leaf_type is None or topic_node['kind'] == leaf_type:
            leaves.append(topic_node)
    else:
        for child in topic_node["children"]:
            leaves += get_all_leaves(topic_node=child, leaf_type=leaf_type)

    return leaves


def get_topic_leaves(topic_id=None, path=None, leaf_type=None):
    """Given a topic (identified by topic_id or path), return all descendant exercises"""
    assert (topic_id or path) and not (topic_id and path), "Specify topic_id or path, not both."

    if not path:
        topic_node = filter(partial(lambda node, name: node['slug'] == name, name=topic_id), get_node_cache('Topic').values())
        if not topic_node:
            return []
        path = topic_node[0]['path']

    topic_node = get_topic_by_path(path)
    exercises = get_all_leaves(topic_node=topic_node, leaf_type=leaf_type)

    return exercises


def get_topic_exercises(*args, **kwargs):
    """Get all exercises for a particular set of topics"""
    kwargs["leaf_type"] = "Exercise"
    return get_topic_leaves(*args, **kwargs)


def get_topic_videos(*args, **kwargs):
    """Get all videos for a particular set of topics"""
    kwargs["leaf_type"] = "Video"
    return get_topic_leaves(*args, **kwargs)


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
        for topic in (topics or get_node_cache('Topic').values()):
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

    topics = get_exercise_topics()["topics"].values()
    topics = sorted(topics, key=lambda k: (k["y"], k["x"]))
    return topics
