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

multipath_kinds = ["Exercise", "Video"]

topics_file = "topics.json"
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
    global NODE_CACHE
    if NODE_CACHE is None or force:
        NODE_CACHE = generate_node_cache(get_topic_tree(force))
    if node_type is None:
        return NODE_CACHE
    else:
        return NODE_CACHE[node_type]


KNOWLEDGEMAP_TOPICS = None
def get_knowledgemap_topics(force=False):
    global KNOWLEDGEMAP_TOPICS, map_layout_file
    if KNOWLEDGEMAP_TOPICS is None or force:
        kmap = json.loads(open(os.path.join(settings.DATA_PATH, map_layout_file)).read())
        KNOWLEDGEMAP_TOPICS = sorted(kmap["topics"].values(), key=lambda k: (k["y"], k["x"]))
    return KNOWLEDGEMAP_TOPICS


ID2SLUG_MAP = None
def get_id2slug_map(force=False):
    global ID2SLUG_MAP, video_remap_file
    if ID2SLUG_MAP is None or force:
        ID2SLUG_MAP     = json.loads(open(os.path.join(settings.DATA_PATH, video_remap_file)).read())
    return ID2SLUG_MAP


FLAT_TOPIC_TREE = None
def get_flat_topic_tree(force=False):
    global FLAT_TOPIC_TREE
    if FLAT_TOPIC_TREE is None or force:
        FLAT_TOPIC_TREE = generate_flat_topic_tree(get_node_cache(force=force))
    return FLAT_TOPIC_TREE


def generate_flat_topic_tree(node_cache=None):
    categories = node_cache or get_node_cache()
    result = dict()
    # make sure that we only get the slug of child of a topic
    # to avoid redundancy
    for category_name, category in categories.iteritems():
        result[category_name] = {}
        for node_name, node in category.iteritems():
            relevant_data = {'title': node['title'],
                             'path': node['path'],
                             'kind': node['kind'],
            }
            result[category_name][node_name] = relevant_data
    return result


def generate_node_cache(topictree=None):#, output_dir=settings.DATA_PATH):
    """
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Video nodes.
    """

    if not topictree:
        topictree = get_topic_tree()
    node_cache = {}


    def recurse_nodes(node, path="/", parents=[]):
        # Add the node to the node cache
        kind = node["kind"]
        node_cache[kind] = node_cache.get(kind, {})
        
        if node["slug"] in node_cache[kind]:
            # Existing node, so append the path to the set of paths
            assert kind in multipath_kinds, "Make sure we expect to see multiple nodes map to the same slug (%s unexpected)" % kind

            # Before adding, let's validate some basic properties of the 
            #   stored node and the new node:
            # 1. Compare the keys, and make sure that they overlap 
            #      (except the stored node will not have 'path', but instead 'paths')
            # 2. For string args, check that values are the same
            #      (most/all args are strings, and ... I feel we're already being darn
            #      careful here.  So, I think it's enough.
            node_shared_keys = set(node.keys()) - set(["path"])
            stored_shared_keys = set(node_cache[kind][node["slug"]]) - set(["path", "paths", "parents"])
            unshared_keys = node_shared_keys.symmetric_difference(stored_shared_keys)
            shared_keys = node_shared_keys.intersection(stored_shared_keys)
            assert not unshared_keys, "Node and stored node should have all the same keys."
            for key in shared_keys:
                # A cursory check on values, for strings only (avoid unsafe types)
                if isinstance(node[key], basestring):
                    assert node[key] == node_cache[kind][node["slug"]][key], "Node values don't match"

            # We already added this node, it's just found at multiple paths.
            #   So, save the new path
            node_cache[kind][node["slug"]]["paths"].append(node["path"])
            node_cache[kind][node["slug"]]["parents"] = list(set(node_cache[kind][node["slug"]]["parents"]).union(set(parents)))

        else:
            # New node, so copy off, massage, and store.
            node_copy = node
            if kind in multipath_kinds:
                # If multiple paths can map to a single slug, need to store all paths.
                node_copy["paths"] = [node_copy["path"]]
            node_cache[kind][node["slug"]] = node_copy
            # Add parents
            node_cache[kind][node["slug"]]["parents"] = parents

        # Do the recursion
        for child in node.get("children", []):
            assert "path" in node and "paths" not in node, "This code can't handle nodes with multiple paths; it just generates them!"
            recurse_nodes(child, node["path"], parents + [node["slug"]])

    recurse_nodes(topictree)

    return node_cache


def get_videos(topic): 
    """Given a topic node, returns all video node children (non-recursively)"""
    return filter(lambda node: node["kind"] == "Video", topic["children"])


def get_exercises(topic): 
    """Given a topic node, returns all exercise node children (non-recursively)"""
    return filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])


def get_live_topics(topic): 
    """Given a topic node, returns all children that are not hidden and contain at least one video (non-recursively)"""
    return filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])


def get_downloaded_youtube_ids(videos_path=settings.CONTENT_ROOT):
    return [path.split("/")[-1].split(".")[0] for path in glob.glob(videos_path + "*.mp4")]


def get_topic_by_path(path, root_node=None):
    """Given a topic path, return the corresponding topic node in the topic hierarchy"""
    # Make sure the root fits
    if not root_node:
        root_node = get_topic_tree()
    if path == root_node["path"]:
        return root_node
    elif not path.startswith(root_node["path"]):
        return {}
        

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

    return cur_node or {}


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


def get_exercise_paths():
    """This function retrieves all the exercise paths.
    """
    exercises = get_node_cache("Exercise").values()
    return [exercise["paths"][0] for exercise in exercises if len(exercise.get("paths", [])) > 0]


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


def get_video_by_youtube_id(youtube_id):
    slug = get_id2slug_map().get(youtube_id, None)
    return get_node_cache("Video")[slug] if slug else None


def is_sibling(node1, node2):
    """
    """
    parse_path = lambda n: n["path"] if not kind_slugs[n["kind"]] else n["path"].split("/" + kind_slugs[n["kind"]])[0]

    parent_path1 = parse_path(node1)
    parent_path2 = parse_path(node2)

    return parent_path1 == parent_path2

