"""
Important constants and helpful functions for the topic tree and a view on its data, the node cache.

The topic tree is a hierarchical representation of real data (exercises, and videos).
Leaf nodes of the tree are real learning resources, such as videos and exercises.
Non-leaf nodes are topics, which describe a progressively higher-level grouping of the topic data.

Each node in the topic tree comes with lots of metadata, including:
* title
* description
* id (unique identifier; now equivalent to slug below)
* slug (for computing a URL)
* path (which is equivalent to a URL)
* kind (Topic, Exercise, Video)
and more.

* get_video_cache() returns all videos
* get_node_cache()["Video"][video_slug] returns all video nodes that contain that video slug.
"""
import glob
import json
import os
import re
from functools import partial

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.utils import translation
from django.utils.translation import ugettext as _

from fle_utils.general import softload_json
from kalite import i18n

TOPICS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "topics.json")
EXERCISES_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "exercises.json")
VIDEOS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "videos.json")
ASSESSMENT_ITEMS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "assessmentitems.json")
KNOWLEDGEMAP_TOPICS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "map_topics.json")
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")

CACHE_VARS = []

if not os.path.exists(settings.CHANNEL_DATA_PATH):
    logging.warning("Channel {channel} does not exist.".format(channel=settings.CHANNEL))


# Globals that can be filled
TOPICS          = None
CACHE_VARS.append("TOPICS")
def get_topic_tree(force=False, props=None):
    global TOPICS, TOPICS_FILEPATH
    if TOPICS is None or force:
        TOPICS = softload_json(TOPICS_FILEPATH, logger=logging.debug, raises=False)
        validate_ancestor_ids(TOPICS)  # make sure ancestor_ids are set properly

        # Limit the memory footprint by unloading particular values
        if props:
            node_cache = get_node_cache()
            for kind, list_by_kind in node_cache.iteritems():
                for node_list in list_by_kind.values():
                    for node in node_list:
                        for att in node.keys():
                            if att not in props:
                                del node[att]
    return TOPICS


NODE_CACHE = None
CACHE_VARS.append("NODE_CACHE")
def get_node_cache(node_type=None, force=False):
    global NODE_CACHE
    if NODE_CACHE is None or force:
        NODE_CACHE = generate_node_cache(get_topic_tree(force))
    if node_type is None:
        return NODE_CACHE
    else:
        return NODE_CACHE[node_type]

EXERCISES          = None
CACHE_VARS.append("EXERCISES")
def get_exercise_cache(force=False):
    global EXERCISES, EXERCISES_FILEPATH
    if EXERCISES is None or force:
        EXERCISES = softload_json(EXERCISES_FILEPATH, logger=logging.debug, raises=False)

    return EXERCISES

VIDEOS          = None
CACHE_VARS.append("VIDEOS")
def get_video_cache(force=False):
    global VIDEOS, VIDEOS_FILEPATH
    if VIDEOS is None or force:
        VIDEOS = softload_json(VIDEOS_FILEPATH, logger=logging.debug, raises=False)

    return VIDEOS

ASSESSMENT_ITEMS          = None
CACHE_VARS.append("ASSESSMENT_ITEMS")
def get_assessment_item_cache(force=False):
    global ASSESSMENT_ITEMS, ASSESSMENT_ITEMS_FILEPATH
    if ASSESSMENT_ITEMS is None or force:
        ASSESSMENT_ITEMS = softload_json(ASSESSMENT_ITEMS_FILEPATH, logger=logging.debug, raises=False)

    return ASSESSMENT_ITEMS

KNOWLEDGEMAP_TOPICS = None
CACHE_VARS.append("KNOWLEDGEMAP_TOPICS")
def get_knowledgemap_topics(force=False):
    global KNOWLEDGEMAP_TOPICS
    if KNOWLEDGEMAP_TOPICS is None or force:
        KNOWLEDGEMAP_TOPICS =  softload_json(KNOWLEDGEMAP_TOPICS_FILEPATH, logger=logging.debug, raises=False)
    return KNOWLEDGEMAP_TOPICS

CONTENT          = None
CACHE_VARS.append("CONTENT")
def get_content_cache(force=False):
    global CONTENT, CONTENT_FILEPATH

    if CONTENT is None or force:
        CONTENT = softload_json(CONTENT_FILEPATH, logger=logging.debug, raises=False)
 
    return CONTENT

SLUG2ID_MAP = None
CACHE_VARS.append("SLUG2ID_MAP")
def get_slug2id_map(force=False):
    global SLUG2ID_MAP
    if SLUG2ID_MAP is None or force:
        SLUG2ID_MAP = generate_slug_to_video_id_map(get_node_cache(force=force))
    return SLUG2ID_MAP


ID2SLUG_MAP = None
CACHE_VARS.append("ID2SLUG_MAP")
def get_id2slug_map(force=False):
    global ID2SLUG_MAP
    if ID2SLUG_MAP is None or force:
        ID2SLUG_MAP = {}
        for slug, id in get_slug2id_map(force=force).iteritems():
            ID2SLUG_MAP[id] = slug
    return ID2SLUG_MAP


FLAT_TOPIC_TREE = None
CACHE_VARS.append("FLAT_TOPIC_TREE")
def get_flat_topic_tree(force=False, lang_code=settings.LANGUAGE_CODE, alldata=False):
    global FLAT_TOPIC_TREE
    if FLAT_TOPIC_TREE is None:
        FLAT_TOPIC_TREE = {
            # The true and false values are for whether we return
            # the complete data for nodes, as given
            # by the alldata parameter
            True: {},
            False: {}
        }
    if not FLAT_TOPIC_TREE[alldata] or lang_code not in FLAT_TOPIC_TREE[alldata] or force:
        FLAT_TOPIC_TREE[alldata][lang_code] = generate_flat_topic_tree(get_node_cache(force=force), lang_code=lang_code, alldata=alldata)
    return FLAT_TOPIC_TREE[alldata][lang_code]


def validate_ancestor_ids(topictree=None):
    """
    Given the KA Lite topic tree, make sure all parent_id and ancestor_ids are stamped
    """

    if not topictree:
        topictree = get_topic_tree()

    def recurse_nodes(node, ancestor_ids=[]):
        # Add ancestor properties
        if not "parent_id" in node:
            node["parent_id"] = ancestor_ids[-1] if ancestor_ids else None
        if not "ancestor_ids" in node:
            node["ancestor_ids"] = ancestor_ids

        # Do the recursion
        for child in node.get("children", []):
            recurse_nodes(child, ancestor_ids=ancestor_ids + [node["id"]])
    recurse_nodes(topictree)

    return topictree


def generate_slug_to_video_id_map(node_cache=None):
    """
    Go through all videos, and make a map of slug to video_id, for fast look-up later
    """

    node_cache = node_cache or get_node_cache()

    slug2id_map = dict()

    # Make a map from youtube ID to video slug
    for video_id, v in node_cache.get('Video', {}).iteritems():
        try:
            assert v["slug"] not in slug2id_map, "Make sure there's a 1-to-1 mapping between slug and video_id"
        except AssertionError as e:
            logging.warn(_("{slug} duplicated in topic tree - overwritten here.").format(slug=v["slug"]))
        slug2id_map[v['slug']] = video_id

    return slug2id_map


def generate_flat_topic_tree(node_cache=None, lang_code=settings.LANGUAGE_CODE, alldata=False):
    translation.activate(lang_code)

    categories = node_cache or get_node_cache()
    result = dict()
    # make sure that we only get the slug of child of a topic
    # to avoid redundancy
    for category_name, category in categories.iteritems():
        result[category_name] = {}
        for node_name, node in category.iteritems():
            if alldata:
                relevant_data = node
            else:
                relevant_data = {
                    'title': _(node['title']),
                    'path': node['path'],
                    'kind': node['kind'],
                    'available': node.get('available', True),
                    'keywords': node.get('keywords', []),
                }
            result[category_name][node_name] = relevant_data

    translation.deactivate()

    return result


def generate_node_cache(topictree=None):
    """
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Video nodes.
    """

    if not topictree:
        topictree = get_topic_tree()
    node_cache = {}
    node_cache["Topic"] = {}


    def recurse_nodes(node):
        # Add the node to the node cache
        kind = node.get("kind", None)
        if kind == "Topic":
            if node["id"] not in node_cache[kind]:
                node_cache[kind][node["id"]] = node

            # Do the recursion
            for child in node.get("children", []):
                recurse_nodes(child)
    recurse_nodes(topictree)

    node_cache["Exercise"] = get_exercise_cache()
    node_cache["Video"] = get_video_cache()
    node_cache["Content"] = get_content_cache()

    return node_cache


def get_ancestor(node, ancestor_id, ancestor_type="Topic"):
    potential_parents = get_node_cache(ancestor_type).get(ancestor_id)
    if not potential_parents:
        return None
    elif len(potential_parents) == 1:
        return potential_parents
    else:
        for pp in potential_parents:
            if node["path"].startswith(pp["path"]):  # find parent by path
                return pp
        return None

def get_parent(node, parent_type="Topic"):
    return get_ancestor(node, ancestor_id=node["parent_id"], ancestor_type=parent_type)

def get_videos(topic):
    """Given a topic node, returns all video node children (non-recursively)"""
    return filter(lambda node: node["kind"] == "Video", topic["children"])


def get_exercises(topic):
    """Given a topic node, returns all exercise node children (non-recursively)"""
    # Note: "live" is currently not stamped on any nodes, but could be in the future, so keeping here.
    return filter(lambda node: node["kind"] == "Exercise" and node.get("live", True), topic["children"])


def get_live_topics(topic):
    """Given a topic node, returns all children that are not hidden and contain at least one video (non-recursively)"""
    # Note: "hide" is currently not stamped on any nodes, but could be in the future, so keeping here.
    return filter(lambda node: node["kind"] == "Topic" and not node.get("hide") and (set(node["contains"]) - set(["Topic"])), topic["children"])


def get_topic_by_path(path, root_node=None):
    """Given a topic path, return the corresponding topic node in the topic hierarchy"""

    # Normalize the path
    path_withslash = path + ("/" if not path.endswith("/") else "")
    path_noslash = path_withslash[:-1]

    if path_noslash:
        slug = path_noslash.split("/")[-1]
    else:
        slug = "root"

    cur_node = get_node_cache()["Topic"].get(slug, {})


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

    elif not leaf_type or leaf_type in topic_node["contains"]:
        for child in topic_node["children"]:
            leaves += get_all_leaves(topic_node=child, leaf_type=leaf_type)

    return leaves


def get_child_topics(topic_node):
    """Return list of immediate children that are topics"""
    topics = []
    if "children" in topic_node:
        for child in topic_node["children"]:
            if child['kind'] == 'Topic':
                topics.append(child['id'])
    return topics


def get_topic_hierarchy(topic_node=get_topic_tree()):
    """
    Return hierarchical list of topics for main nav
    """
    topic_hierarchy = {
        "id": topic_node['id'],
        "title": topic_node['title'],
        "description": topic_node['description'],
    }
    if ("children" in topic_node) and ('Topic' in topic_node['contains']):
        topic_hierarchy["children"] = []
        for child in topic_node['children']:
            if child['kind'] == 'Topic':
                topic_hierarchy["children"].append(get_topic_hierarchy(child))

    return topic_hierarchy

def dump_topic_hierarchy():
    """Dump topic hierarchy to JSON"""
    topic_hierarchy = get_topic_hierarchy()
    with open('topic_hierarchy.json', 'w') as outfile:
        json.dump(topic_hierarchy, outfile, indent=4, sort_keys=True)


def get_topic_leaves(topic_id=None, path=None, leaf_type=None):
    """Given a topic (identified by topic_id or path), return all descendent leaf nodes"""
    assert (topic_id or path) and not (topic_id and path), "Specify topic_id or path, not both."

    if not path:
        topic_node = get_node_cache('Topic').get(topic_id, None)
        if not topic_node:
            return []
        else:
            path = topic_node['path']

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
        if video.get("related_exercise"):
            related_exercises.append(video['related_exercise'])
    return related_exercises


def get_exercise_paths():
    """This function retrieves all the exercise paths.
    """
    exercises = get_node_cache("Exercise").values()
    return [n["path"] for exercise in exercises for n in exercise]


def garbage_get_related_videos(exercises, topics=None, possible_videos=None):
    """Given a set of exercises, get all of the videos that say they're related.

    possible_videos: list of videos to consider.
    topics: if not possible_videos, then get the possible videos from a list of topics.
    """
    assert bool(topics) + bool(possible_videos) <= 1, "May specify possible_videos or topics, but not both."

    related_videos = []

    if not possible_videos:
        possible_videos = []
        for topic in (topics or get_node_cache('Topic').values()):
            possible_videos += get_topic_videos(topic_id=topic['id'])

    # Get exercises from videos
    exercise_ids = [ex["id"] for ex in exercises]
    for video in possible_videos:
        if "related_exercise" in video and video["related_exercise"]['id'] in exercise_ids:
            related_videos.append(video)
    return related_videos


def get_related_videos(exercise, limit_to_available=True):
    """
    Return topic tree cached data for each related video.
    """
    # Find related videos
    related_videos = {}
    for slug in exercise["related_video_slugs"]:
        video_node = get_node_cache("Video").get(get_slug2id_map().get(slug, ""), {})

        # Make sure the IDs are recognized, and are available.
        if video_node and (not limit_to_available or video_node.get("available", False)):
            related_videos[slug] = video_node

    return related_videos



def is_base_leaf(node, is_base_leaf=True):
    """Return true if the topic node has no child topic nodes"""
    for child in node['children']:
        if child['kind'] == 'Topic':
            return False
    return is_base_leaf


def get_neighbor_nodes(node, neighbor_kind=None):

    parent = get_parent(node)
    prev = next = None
    filtered_children = [ch for ch in parent["children"] if not neighbor_kind or ch["kind"] == neighbor_kind]

    for idx, child in enumerate(filtered_children):
        if child["path"] != node["path"]:
            continue

        if idx < (len(filtered_children) - 1):
            next = filtered_children[idx + 1]
        if idx > 0:
            prev = filtered_children[idx - 1]
        break

    return prev, next

def get_video_page_paths(video_id=None):
    try:
        return [n["path"] for n in get_node_cache("Video")[video_id]]
    except:
        return []


def get_exercise_page_paths(video_id=None):

    try:
        exercise_paths = set()
        for exercise in get_related_exercises(videos=get_node_cache("Video")[video_id]):
            exercise_paths = exercise_paths.union(set([exercise["path"]]))
        return list(exercise_paths)
    except Exception as e:
        logging.debug("Exception while getting exercise paths: %s" % e)
        return []

def get_exercise_data(request, exercise_id=None):
    exercise = get_exercise_cache().get(exercise_id, None)

    if not exercise:
        return None

    exercise_root = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
    exercise_file = exercise["slug"] + ".html"
    exercise_template = exercise_file

    # Get the language codes for exercise templates that exist
    exercise_path = partial(lambda lang, slug, eroot: os.path.join(eroot, lang, slug + ".html"), slug=exercise["slug"], eroot=exercise_root)
    code_filter = partial(lambda lang, eroot, epath: os.path.isdir(os.path.join(eroot, lang)) and os.path.exists(epath(lang)), eroot=exercise_root, epath=exercise_path)
    available_langs = set(["en"] + [lang_code for lang_code in os.listdir(exercise_root) if code_filter(lang_code)])

    # Return the best available exercise template
    exercise_lang = i18n.select_best_available_language(request.language, available_codes=available_langs)
    if exercise_lang == "en":
        exercise_template = exercise_file
    else:
        exercise_template = exercise_path(exercise_lang)[(len(exercise_root) + 1):]

    exercise["lang"] = exercise_lang
    exercise["template"] = exercise_template

    return exercise


def get_video_data(request, video_id=None):

    video_cache = get_video_cache()
    video = video_cache.get(video_id, None)

    if not video:
        return None

    # TODO-BLOCKER(jamalex): figure out why this video data is not prestamped, and remove this:
    from kalite.updates import stamp_availability_on_video
    video = stamp_availability_on_video(video)

    if not video["available"]:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this video in the topic tree
            messages.warning(request, _("This video was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This video was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This video was not found! You must login as an admin/teacher to download the video."))

    # Fallback mechanism
    available_urls = dict([(lang, avail) for lang, avail in video["availability"].iteritems() if avail["on_disk"]])
    if video["available"] and not available_urls:
        vid_lang = "en"
        messages.success(request, "Got video content from %s" % video["availability"]["en"]["stream"])
    else:
        vid_lang = i18n.select_best_available_language(request.language, available_codes=available_urls.keys())

    # TODO(jamalex): clean this up; we're flattening it here so handlebars can handle it more easily
    video = video.copy()
    video["video_urls"] = video["availability"].get(vid_lang)
    video["subtitle_urls"] = video["availability"].get(vid_lang, {}).get("subtitles")
    video["selected_language"] = vid_lang
    video["dubs_available"] = len(video["availability"]) > 1
    video["title"] = _(video["title"])
    video["description"] = _(video.get("description", ""))
    video["video_id"] = video["id"]

    return video

def get_assessment_item_data(request, assessment_item_id=None):
    assessment_item = get_assessment_item_cache().get(assessment_item_id, None)

    if not assessment_item:
        return None

    # TODO (rtibbles): Enable internationalization for the assessment_items.

    return assessment_item

def get_content_data(request, content_id=None):

    content_cache = get_content_cache()
    content = content_cache.get(content_id, None)

    if not content:
        return None

    # TODO-BLOCKER(jamalex): figure out why this content data is not prestamped, and remove this:
    from kalite.updates import stamp_availability_on_content
    content = stamp_availability_on_content(content)

    if not content["available"]:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this content in the topic tree
            messages.warning(request, _("This content was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This content was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This content was not found! You must login as an admin/teacher to download the content."))

    # Fallback mechanism
    available_urls = dict([(lang, avail) for lang, avail in content["availability"].iteritems() if avail["on_disk"]])
    if content["available"] and not available_urls:
        content_lang = "en"
        messages.success(request, "Got content content from %s" % content["availability"]["en"]["stream"])
    else:
        content_lang = i18n.select_best_available_language(request.language, available_codes=available_urls.keys())

    # TODO(jamalex): clean this up; we're flattening it here so handlebars can handle it more easily
    content = content.copy()
    content["content_urls"] = content["availability"].get(content_lang)
    content["selected_language"] = content_lang
    content["trans_available"] = len(content["availability"]) > 1
    content["title"] = _(content["title"])
    content["description"] = _(content.get("description", ""))
    content["content_id"] = content["id"]

    return content



def video_dict_by_video_id(flat_topic_tree=None):
    # TODO (aron): Add i18n by varying the language of the topic tree here
    topictree = flat_topic_tree if flat_topic_tree else get_flat_topic_tree()

    # since videos in the flat topic tree are indexed by youtube
    # number, we have to construct another dict with the id
    # instead as the key
    video_title_dict = {}
    video_id_regex = re.compile('.*/v/(?P<entity_id>.*)/')
    for video_node in topictree['Video'].itervalues():
        video_id_matches = re.match(video_id_regex, video_node['path'])
        if video_id_matches:
            video_key = video_id_matches.groupdict()['entity_id']
            video_title_dict[video_key] = video_node

    return video_title_dict

def convert_leaf_url_to_id(leaf_url):
    """Strip off the /e/ or /v/ and trailing slash from a leaf url and leave only the ID"""
    leaf_id = [x for x in leaf_url.split("/") if len(x) > 1]
    assert(len(leaf_id) == 1), "Something in leaf ID is malformed: %s" % leaf_url
    return leaf_id[0]


