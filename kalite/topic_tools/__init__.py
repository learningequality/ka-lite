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
"""
import os
import re
from functools import partial

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.utils import translation
from django.utils.translation import ugettext as _

from fle_utils.general import softload_json
from kalite import i18n

TOPICS_FILEPATHS = {
    settings.CHANNEL: os.path.join(settings.CHANNEL_DATA_PATH, "topics.json")
}
EXERCISES_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "exercises.json")
ASSESSMENT_ITEMS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "assessmentitems.json")
KNOWLEDGEMAP_TOPICS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "map_topics.json")
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")

CACHE_VARS = []

if not os.path.exists(settings.CHANNEL_DATA_PATH):
    logging.warning("Channel {channel} does not exist.".format(channel=settings.CHANNEL))


# Globals that can be filled
TOPICS          = {}
CACHE_VARS.append("TOPICS")
def get_topic_tree(force=False, annotate=False, channel=settings.CHANNEL):
    global TOPICS, TOPICS_FILEPATHS
    if TOPICS.get(channel) is None or force:
        TOPICS[channel] = softload_json(TOPICS_FILEPATHS.get(channel), logger=logging.debug, raises=False)
        validate_ancestor_ids(TOPICS[channel])  # make sure ancestor_ids are set properly

    if annotate:
        content_cache = get_content_cache()
        def recurse_nodes(node):
            # By default this is very charitable, assuming if something has not been annotated it is available
            if content_cache.get(node.get("id"), {}).get("languages", [""]):
                node["available"] = True
            # Do the recursion
            for child in node.get("children", []):
                recurse_nodes(child)
        recurse_nodes(TOPICS[channel])

    return TOPICS[channel]


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


LEAFED_TOPICS = None
CACHE_VARS.append("LEAFED_TOPICS")
def get_leafed_topics(force=False):
    global LEAFED_TOPICS
    if LEAFED_TOPICS is None or force:
        LEAFED_TOPICS = [topic for topic in get_node_cache()["Topic"].values() if [child for child in topic.get("children", []) if child.get("kind") != "Topic"]]
    return LEAFED_TOPICS

def create_thumbnail_url(thumbnail):
    if is_content_on_disk(thumbnail, "png"):
        return settings.CONTENT_URL + thumbnail + ".png"
    elif is_content_on_disk(thumbnail, "jpg"):
        return settings.CONTENT_URL + thumbnail + ".jpg"
    return None

CONTENT          = None
CACHE_VARS.append("CONTENT")
def get_content_cache(force=False, annotate=False):
    global CONTENT, CONTENT_FILEPATH

    if CONTENT is None or force:
        CONTENT = softload_json(CONTENT_FILEPATH, logger=logging.debug, raises=False)
    
    if annotate:
        for content in CONTENT.values():
            languages = []
            default_thumbnail = create_thumbnail_url(content.get("id"))
            dubmap = i18n.get_id2oklang_map(content.get("id"))
            for lang, dubbed_id in dubmap.items():
                # TODO (rtibbles): Explicitly stamp "mp4" on KA videos in contentload
                format = content.get("format", "mp4")
                if is_content_on_disk(dubbed_id, format):
                    languages.append(lang)
                    thumbnail = create_thumbnail_url(dubbed_id) or default_thumbnail
                    content["lang_data_" + lang] = {
                        "stream": settings.CONTENT_URL + dubmap.get(lang) + "." + format,
                        "stream_type": "{kind}/{format}".format(kind=content.get("kind", "").lower(), format=format),
                        "thumbnail": thumbnail,
                    }
            content["languages"] = languages
            subtitle_lang_codes = [lc for lc in os.listdir(i18n.get_srt_path()) if os.path.exists(i18n.get_srt_path(lc, content.get("id")))]
            subtitle_urls = [{
                "code": lc,
                "url": settings.STATIC_URL + "srt/{code}/subtitles/{id}.srt".format(code=lc, id=content.get("id")),
                "name": i18n.get_language_name(lc)
                } for lc in subtitle_lang_codes if os.path.exists(i18n.get_srt_path(lc, content.get("id")))]
            content["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

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
    for content_id, c in node_cache.get('Content', {}).iteritems():
        try:
            assert c["slug"] not in slug2id_map, "Make sure there's a 1-to-1 mapping between slug and content_id"
        except AssertionError as e:
            logging.warn(_("{slug} duplicated in topic tree - overwritten here.").format(slug=c["slug"]))
        slug2id_map[c['slug']] = content_id

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
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Content nodes.
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
    node_cache["Content"] = get_content_cache()

    return node_cache

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

    content_lang = i18n.select_best_available_language(request.language, available_codes=content.get("languages", [])) or ""
    urls = content.get("lang_data_" + content_lang, None)

    if not urls:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this content in the topic tree
            messages.warning(request, _("This content was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This content was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This content was not found! You must login as an admin/teacher to download the content."))

    # TODO(jamalex): clean this up; we're flattening it here so handlebars can handle it more easily
    content = content.copy()
    content["content_urls"] = urls
    content["selected_language"] = content_lang
    content["title"] = _(content["title"])
    content["description"] = _(content.get("description", ""))

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


def is_content_on_disk(content_id, format="mp4", content_path=None):
    content_path = content_path or settings.CONTENT_ROOT
    content_file = os.path.join(content_path, content_id + ".%s" % format)
    return os.path.isfile(content_file)