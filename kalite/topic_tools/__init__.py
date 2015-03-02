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
import json
import copy
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
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")

CACHE_VARS = []

if not os.path.exists(settings.CHANNEL_DATA_PATH):
    logging.warning("Channel {channel} does not exist.".format(channel=settings.CHANNEL))


# Globals that can be filled
TOPICS          = None
CACHE_VARS.append("TOPICS")
def get_topic_tree(force=False, annotate=False, channel=settings.CHANNEL, language=settings.LANGUAGE_CODE):
    global TOPICS, TOPICS_FILEPATHS
    if not TOPICS:
        TOPICS = {}
    if TOPICS.get(channel) is None:
        TOPICS[channel] = {}
    if TOPICS.get(channel, {}).get(language) is None:
        TOPICS[channel][language] = softload_json(TOPICS_FILEPATHS.get(channel), logger=logging.debug, raises=False)

        # Just loaded from disk, so have to restamp.
        annotate = True

    if annotate:
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            topics = softload_json(TOPICS_FILEPATHS.get(channel) + "_" + language + ".cache", logger=logging.debug, raises=False)
            if topics:
                TOPICS[channel][language] = topics
                return TOPICS[channel][language]

        # Loop through all the nodes in the topic tree
        # and cross reference with the content_cache to check availability.
        content_cache = get_content_cache(language=language)
        exercise_cache = get_exercise_cache(language=language)
        def recurse_nodes(node):

            child_availability = []

            # Do the recursion
            for child in node.get("children", []):
                recurse_nodes(child)
                child_availability.append(child.get("available", False))

            # If child_availability is empty then node has no children so we can determine availability
            if child_availability:
                node["available"] = any(child_availability)
            else:
                # By default this is very charitable, assuming if something has not been annotated
                # it is available.
                if node.get("kind") == "Exercise":
                    cache_node = exercise_cache.get(node.get("id"), {})
                else:
                    cache_node = content_cache.get(node.get("id"), {})
                node["available"] = cache_node.get("available", True)

            # Translate everything for good measure
            with i18n.translate_block(language):
                node["title"] = _(node.get("title", ""))
                node["description"] = _(node.get("description", "")) if node.get("description") else ""

        recurse_nodes(TOPICS[channel][language])
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
            try:
                with open(TOPICS_FILEPATHS.get(channel) + "_" + language + ".cache", "w") as f:
                    json.dump(TOPICS[channel][language], f)
            except IOError as e:
                logging.warn("Annotated topic cache file failed in saving with error {e}".format(e=e))

    return TOPICS[channel][language]


NODE_CACHE = None
CACHE_VARS.append("NODE_CACHE")
def get_node_cache(node_type=None, force=False, language=settings.LANGUAGE_CODE):
    global NODE_CACHE
    if NODE_CACHE is None or force:
        NODE_CACHE = generate_node_cache()
    if node_type is None:
        return NODE_CACHE
    else:
        return NODE_CACHE[node_type]

EXERCISES          = None
CACHE_VARS.append("EXERCISES")
def get_exercise_cache(force=False, language=settings.LANGUAGE_CODE):
    global EXERCISES, EXERCISES_FILEPATH
    if EXERCISES is None:
        EXERCISES = {}
    if EXERCISES.get(language) is None:
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            exercises = softload_json(EXERCISES_FILEPATH + "_" + language + ".cache", logger=logging.debug, raises=False)
            if exercises:
                EXERCISES[language] = exercises
                return EXERCISES[language]
        EXERCISES[language] = softload_json(EXERCISES_FILEPATH, logger=logging.debug, raises=False)
        exercise_root = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
        if os.path.exists(exercise_root):
            exercise_templates = os.listdir(exercise_root)
        else:
            exercise_templates = []
        assessmentitems = get_assessment_item_cache()
        TEMPLATE_FILE_PATH = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s")
        for exercise in EXERCISES[language].values():
            exercise_file = exercise["name"] + ".html"
            exercise_template = exercise_file

            # Get the language codes for exercise templates that exist
            available_langs = set(["en"] + [lang_code for lang_code in exercise_templates if os.path.exists(os.path.join(exercise_root, lang_code, exercise_file))])

            # Return the best available exercise template
            exercise_lang = i18n.select_best_available_language(language, available_codes=available_langs)
            if exercise_lang == "en":
                exercise_template = exercise_file
            else:
                exercise_template = os.path.join(exercise_lang, exercise_file)

            if exercise.get("uses_assessment_items", False):
                available = False
                items = []
                for item in exercise.get("all_assessment_items","[]"):
                    item = json.loads(item)
                    if assessmentitems.get(item.get("id")):
                        items.append(item)
                        available = True
                exercise["all_assessment_items"] = items
            else:
                available = os.path.isfile(TEMPLATE_FILE_PATH % exercise_template)

            with i18n.translate_block(exercise_lang):
                exercise["available"] = available
                exercise["lang"] = exercise_lang
                exercise["template"] = exercise_template
                exercise["title"] = _(exercise.get("title", ""))
                exercise["description"] = _(exercise.get("description", "")) if exercise.get("description") else ""

        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
            try:
                with open(EXERCISES_FILEPATH + "_" + language + ".cache", "w") as f:
                    json.dump(EXERCISES[language], f)
            except IOError as e:
                logging.warn("Annotated exercise cache file failed in saving with error {e}".format(e=e))

    return EXERCISES[language]

ASSESSMENT_ITEMS          = None
CACHE_VARS.append("ASSESSMENT_ITEMS")
def get_assessment_item_cache(force=False):
    global ASSESSMENT_ITEMS, ASSESSMENT_ITEMS_FILEPATH
    if ASSESSMENT_ITEMS is None or force:
        ASSESSMENT_ITEMS = softload_json(ASSESSMENT_ITEMS_FILEPATH, logger=logging.debug, raises=False)

    return ASSESSMENT_ITEMS

def recurse_topic_tree_to_create_hierarchy(node, level_cache={}, hierarchy=[]):
    if not level_cache:
        for hier in hierarchy:
            level_cache[hier] = []
    render_type = node.get("render_type", "")
    if render_type in hierarchy:
        node_copy = copy.deepcopy(dict(node))
        for child in node_copy.get("children", []):
            if "children" in child:
                del child["children"]
        level_cache[render_type].append(node_copy)
    for child in node.get("children", []):
        recurse_topic_tree_to_create_hierarchy(child, level_cache, hierarchy=hierarchy)
    return level_cache

KNOWLEDGEMAP_TOPICS = None
CACHE_VARS.append("KNOWLEDGEMAP_TOPICS")
def get_knowledgemap_topics(force=False, language=settings.LANGUAGE_CODE):
    global KNOWLEDGEMAP_TOPICS
    if KNOWLEDGEMAP_TOPICS is None:
        KNOWLEDGEMAP_TOPICS = {}
    if KNOWLEDGEMAP_TOPICS.get(language) is None or force:
        KNOWLEDGEMAP_TOPICS[language] = recurse_topic_tree_to_create_hierarchy(get_topic_tree(language=language), {}, hierarchy=["Domain", "Subject", "Topic", "Tutorial"])["Topic"]
    return KNOWLEDGEMAP_TOPICS[language]


LEAFED_TOPICS = None
CACHE_VARS.append("LEAFED_TOPICS")
def get_leafed_topics(force=False, language=settings.LANGUAGE_CODE):
    global LEAFED_TOPICS
    if LEAFED_TOPICS is None or force:
        LEAFED_TOPICS = [topic for topic in get_node_cache(language=language)["Topic"].values() if [child for child in topic.get("children", []) if child.get("kind") != "Topic"]]
    return LEAFED_TOPICS

def create_thumbnail_url(thumbnail):
    if is_content_on_disk(thumbnail, "png"):
        return settings.CONTENT_URL + thumbnail + ".png"
    elif is_content_on_disk(thumbnail, "jpg"):
        return settings.CONTENT_URL + thumbnail + ".jpg"
    return None

CONTENT          = None
CACHE_VARS.append("CONTENT")
def get_content_cache(force=False, annotate=False, language=settings.LANGUAGE_CODE):
    global CONTENT, CONTENT_FILEPATH

    if CONTENT is None:
        CONTENT = {}
    if CONTENT.get(language) is None:
        CONTENT[language] = softload_json(CONTENT_FILEPATH, logger=logging.debug, raises=False)
        annotate = True
    
    if annotate:
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            content = softload_json(CONTENT_FILEPATH + "_" + language + ".cache", logger=logging.debug, raises=False)
            if content:
                CONTENT[language] = content
                return CONTENT[language]

        # Loop through all content items and put thumbnail urls, content urls,
        # and subtitle urls on the content dictionary, and list all languages
        # that the content is available in.
        for content in CONTENT[language].values():
            default_thumbnail = create_thumbnail_url(content.get("id"))
            dubmap = i18n.get_id2oklang_map(content.get("id"))
            if dubmap:
                content_lang = i18n.select_best_available_language(language, available_codes=dubmap.keys()) or ""
                if content_lang:
                    dubbed_id = dubmap.get(content_lang)
                    format = content.get("format", "")
                    if is_content_on_disk(dubbed_id, format):
                        content["available"] = True
                        thumbnail = create_thumbnail_url(dubbed_id) or default_thumbnail
                        content["content_urls"] = {
                            "stream": settings.CONTENT_URL + dubmap.get(content_lang) + "." + format,
                            "stream_type": "{kind}/{format}".format(kind=content.get("kind", "").lower(), format=format),
                            "thumbnail": thumbnail,
                        }
                    else:
                        content["available"] = False
                else:
                    content["available"] = False
            else:
                content["available"] = False

            # Get list of subtitle language codes currently available
            subtitle_lang_codes = [] if not os.path.exists(i18n.get_srt_path()) else [lc for lc in os.listdir(i18n.get_srt_path()) if os.path.exists(i18n.get_srt_path(lc, content.get("id")))]

            # Generate subtitle URLs for any subtitles that do exist for this content item
            subtitle_urls = [{
                "code": lc,
                "url": settings.STATIC_URL + "srt/{code}/subtitles/{id}.srt".format(code=lc, id=content.get("id")),
                "name": i18n.get_language_name(lc)
                } for lc in subtitle_lang_codes if os.path.exists(i18n.get_srt_path(lc, content.get("id")))]

            # Sort all subtitle URLs by language code
            content["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

            with i18n.translate_block(content_lang):
                content["selected_language"] = content_lang
                content["title"] = _(content["title"])
                content["description"] = _(content.get("description", "")) if content.get("description") else ""

        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
            try:
                with open(CONTENT_FILEPATH + "_" + language + ".cache", "w") as f:
                    json.dump(CONTENT[language], f)
            except IOError as e:
                logging.warn("Annotated content cache file failed in saving with error {e}".format(e=e))

    return CONTENT[language]

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
        FLAT_TOPIC_TREE[alldata][lang_code] = generate_flat_topic_tree(get_node_cache(force=force, language=lang_code), lang_code=lang_code, alldata=alldata)
    return FLAT_TOPIC_TREE[alldata][lang_code]


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
    with i18n.translate_block(lang_code):

        categories = node_cache or get_node_cache(language=i18n.lcode_to_django_lang(lang_code))
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

    return result


def generate_node_cache(topictree=None, language=settings.LANGUAGE_CODE):
    """
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Content nodes.
    """

    if not topictree:
        topictree = get_topic_tree(language=language)
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

    node_cache["Exercise"] = get_exercise_cache(language=language)
    node_cache["Content"] = get_content_cache(language=language)

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
    exercise = get_exercise_cache(language=request.language).get(exercise_id, None)

    if not exercise:
        return None

    return exercise


def get_assessment_item_data(request, assessment_item_id=None):
    assessment_item = get_assessment_item_cache().get(assessment_item_id, None)

    if not assessment_item:
        return None

    # TODO (rtibbles): Enable internationalization for the assessment_items.

    return assessment_item

def get_content_data(request, content_id=None):

    content_cache = get_content_cache(language=request.language)
    content = content_cache.get(content_id, None)

    if not content:
        return None

    if not content.get("content_urls", None):
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this content in the topic tree
            messages.warning(request, _("This content was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This content was not found! Please contact your coach or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This content was not found! You must login as an admin/coach to download the content."))

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


###
# Returns a dictionary with each subtopic and their related
# topics.
#
# @param temp_index: a temporary index for comparison tests
###
import time
def generate_recommendation_data(temp_index):

    #hardcoded data, each subtopic is the key with its related subtopics and current courses as the values
    data = {};
    
    data_hardcoded = {
        "early-math": {"related_subtopics": ["early-math", "arithmetic", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "arithmetic": {"related_subtopics": ["arithmetic", "pre-algebra", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "pre-algebra": {"related_subtopics": ["pre-algebra", "algebra", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "algebra": {"related_subtopics": ["algebra", "geometry", "recreational-math", "competition-math", "chemistry"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy"]},
        "geometry": {"related_subtopics": ["geometry", "algebra2", "recreational-math", "competition-math", "chemistry"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy"]},
        "algebra2": {"related_subtopics": ["algebra2", "trigonometry", "probability", "competition-math", "chemistry", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "trigonometry": {"related_subtopics": ["trigonometry", "linear-algebra", "precalculus", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "probability": {"related_subtopics": ["probability", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "precalculus": {"related_subtopics": ["precalculus", "differential calculus", "probability"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "differential-calculus": {"related_subtopics": ["differential-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "integral-calculus": {"related_subtopics": ["integral-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "multivariate-calculus": {"related_subtopics": ["multivariate-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "differential-equations": {"related_subtopics": ["differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "linear-algebra": {"related_subtopics": ["linear-algebra", "precalculus"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "recreational-math": {"related_subtopics": ["recreational-math", "pre-algebra", "algebra", "geometry", "algebra2"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "competition-math": {"related_subtopics": ["competition-math","algebra", "geometry", "algebra2"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},


        "biology": {"related_subtopics": ["biology", "health-and-medicine", "CAS-biodiversity", "Exploratorium", "chemistry", "physics", "cosmology-and-astronomy", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "physics": {"related_subtopics": ["physics", "discoveries-projects", "cosmology-and-astronomy", "nasa", "Exploratorium", "biology", "CAS-biodiversity", "health-and-medicine", "differential-calculus"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "chemistry": {"related_subtopics": ["chemistry", "organic-chemistry", "biology", "health-and-medicine", "physics", "cosmology-and-astronomy", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "organic-chemistry": {"related_subtopics": ["organic-chemistry", "biology", "health-and-medicine", "physics", "cosmology-and-astronomy", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "cosmology-and-astronomy": {"related_subtopics": ["cosmology-and-astronomy", "nasa", "chemistry", "biology", "health-and-medicine", "physics", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "health-and-medicine": {"related_subtopics": ["health-and-medicine", "biology", "chemistry", "CAS-biodiversity", "Exploratorium", "physics", "cosmology-and-astronomy", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "discoveries-projects": {"related_subtopics": ["discoveries-projects", "physics", "computing", "cosmology-and-astronomy", "nasa", "Exploratorium", "biology", "CAS-biodiversity", "health-and-medicine", "differential-calculus"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},

        "microeconomics": {"related_subtopics": ["microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "macroeconomics": {"related_subtopics": ["macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "core-finance": {"related_subtopics": ["core-finance", "entrepreneurship2", "macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "entrepreneurship2": {"related_subtopics": ["entrepreneurship2", "core-finance", "macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},

        "history": {"related_subtopics": ["history", "art-history", "american-civics-subject", "asian-art-museum", "Exploratorium"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "art-history": {"related_subtopics": ["art-history", "ap-art-history", "asian-art-museum", "history", "american-civics-subject", "Exploratorium"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "american-civics-subject": {"related_subtopics": ["american-civics-subject", "history"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "music": {"related_subtopics": ["music"], "unrelated_subtopics": ["biology", "health-and-medicine"]},
        "philosophy": {"related_subtopics": ["philosophy"]},

        "computing": {"related_subtopics": ["computing", "early-math", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math", "biology", "physics", "chemistry", "organic-chemistry", "health-and-medicine", "discoveries-projects", "microeconomics", "macroeconomics", "core-finance", "music"]},

        "sat": {"related_subtopics": ["sat", "arithmetic", "pre-algebra", "algebra", "algebra2", "geometry", "probability", "recreational-math"]},
        "mcat": {"related_subtopics": ["mcat", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine"]},
        "NCLEX-RN": {"related_subtopics": ["NCLEX-RN", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine"]},
        "gmat": {"related_subtopics": ["gmat", "arithmetic", "pre-algebra", "algebra", "algebra2" "geometry", "probability", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "history", "microeconomics", "macroeconomics"]},
        "cahsee-subject": {"related_subtopics": ["cahsee-subject", "early-math", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math"]},
        "iit-jee-subject": {"related_subtopics": ["iit-jee-subject", "arithmetic", "pre-algebra", "geometry", "differential-equations", "differential-calculus", "integral-calculus", "linear-algebra", "probability", "chemistry", "physics", "organic-chemistry"]},
        "ap-art-history": {"related_subtopics": ["ap-art-history", "art-history", "history"]},

        "CAS-biodiversity": {"related_subtopics": ["CAS-biodiversity", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "Exploratorium"]},
        "Exploratorium": {"related_subtopics": ["Exploratorium", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "CAS-biodiversity", "art-history", "music"]},
        "asian-art-museum": {"related_subtopics": ["asian-art-museum", "art-history", "history", "ap-art-history"]},
        "ssf-cci": {"related_subtopics": ["ssf-cci", "art-history", "history"]},
    }


    '''t0 = time.clock()'''


    ### populate data exploiting structure of topic tree ###
    tree = get_topic_tree() #Is there a better way of getting the tree without calling get_topic_tree() again and again?

    '''print 'time taken to create topic_tree: ' + str(time.clock() - t0)
    t1 = time.clock() #running time of actual alg'''

    ##
    # ITERATION 1 - grabs all immediate neighbors of each subtopic
    ##

    #array indices for the current topic and subtopic
    topic_index = 0
    subtopic_index = 0

    #for each topic 
    for topic in tree['children']:

        subtopic_index = 0

        #for each subtopic add the neighbors at distance 1 (2 for each)
        for subtopic in topic['children']:

            neighbors_dist_1 = get_neighbors_at_dist_1(topic_index, subtopic_index, tree)

            #add to data - distance 0 (itself) + distance 1
            data[ subtopic['id'] ] = { 'related_subtopics' : ([subtopic['id']] + neighbors_dist_1) }
            subtopic_index+=1
            
        topic_index+=1


    ##
    # ITERATION 2 - grabs all subsequent neighbors of each subtopic via 
    # Breadth-first search (BFS)
    ##

    #loop through all subtopics currently in data dict
    for subtopic in data:
        related = data[subtopic]['related_subtopics'] # list of related subtopics (right now only 2)
        other_neighbors = get_subsequent_neighbors(related, data)
        data[subtopic]['related_subtopics'] += other_neighbors

    '''print 'time taken for actual algorithm exlcuding topic_tree: ' + str(time.clock() - t1)'''

    #0 is for hardcoded data ###### DELETE AFTER TESTS ########
    if(temp_index == 0):
        return data_hardcoded

    return data



### 
# Returns a lookup table that contains a list of related
# EXERCISES for each subtopic.
#
# @param data: a dicitonary with each subtopic and its related subtopics
###
def get_recommendation_tree(data):
    recommendation_tree = {}  # tree to return

    #loop through all subtopics passed in data
    for subtopic in data:
        recommendation_tree[str(subtopic)] = [] #initialize an empty list for the current s.t.

        related_subtopics = data[subtopic]['related_subtopics'] #list of related subtopic ids

        #loop through all of the related subtopics
        for rel_subtopic in related_subtopics:
            exercises = get_topic_exercises(rel_subtopic)

            for ex in exercises:
                recommendation_tree[str(subtopic)].append(ex['id'])

    return recommendation_tree
      


###
# Returns a list of recommended exercise ids given a
# subtopic id.
#
# @param subtopic_id: the subtopic id (e.g. 'early-math')
###
def get_recommended_exercises(subtopic_id):

    #get a recommendation lookup tree
    tree = get_recommendation_tree(generate_recommendation_data())

    #currently returning everything, perhaps we should just limit the
    #recommendations to a set amount??
    return tree[subtopic_id]



###
# Helper function for generating recommendation data using the topic tree.
# Returns a list of the neihbors at distance 1 from the specified subtopic.
#
# @param topic: the index of the topic that the subtopic belongs to (e.g. math, sciences)
#        subtopic: the index of the subtopic to find the neighbors for
###
def get_neighbors_at_dist_1(topic, subtopic, tree):
    neighbors = []  #neighbor list to be returned
    topic_index = topic #store topic index
    topic = tree['children'][topic] #subtree rooted at the topic that we are looking at
    #curr_subtopic = tree['children'][topic]['children'][subtopic]['id'] #id of topic passed in

    #pointers to the previous and next subtopic (list indices)
    prev = subtopic - 1 
    next = subtopic + 1

    #if there is a previous topic (neighbor to left)
    if(prev > -1 ):
        neighbors.append(topic['children'][prev]['id']) # neighbor on the left side

    #else check if there is a neighboring topic (left)    
    else:
        if (topic_index-1) > -1:
            neighbor_length = len(tree['children'][(topic_index-1)]['children'])
            neighbors.append(tree['children'][(topic_index-1)]['children'][(neighbor_length-1)]['id'])

        else:
            neighbors.append(' ') # no neighbor to the left

    #if there is a neighbor to the right
    if(next < len(topic['children'])):
        neighbors.append(topic['children'][next]['id']) # neighbor on the right side

    #else check if there is a neighboring topic (right)
    else:
        if (topic_index + 1) < len(tree['children']):
            neighbors.append(tree['children'][(topic_index+1)]['children'][0]['id'])

        else:
            neighbors.append(' ') # no neighbor on right side


    return neighbors



###
# Performs Breadth-first search given recommendation data.
# Returns neighbors of a node in order of increasing distance.
# 
# @param nearest_neighbors: array holding the current left and right neighbors (always 2)
# @param data: dictionary of subtopics and their neighbors at distance 1
###

def get_subsequent_neighbors(nearest_neighbors, data):
    left = nearest_neighbors[1]  # subtopic id string of left neighbor
    right = nearest_neighbors[2]

    other_neighbors = []

    # Loop while there are still neighbors
    while left != ' ' or right != ' ':

        # If there is a left neighbor, append its left neighbor
        if left != ' ':
            if data[left]['related_subtopics'][1] != ' ':
                other_neighbors.append(data[left]['related_subtopics'][1])
            left = data[left]['related_subtopics'][1]

        # Repeat for right neighbor
        if right != ' ':
            if data[right]['related_subtopics'][2] != ' ':
                other_neighbors.append(data[right]['related_subtopics'][2])
            right = data[right]['related_subtopics'][2]

    return other_neighbors


###
# Tester that will compare the similarity and accuracy of both 
# content recommendation algorithms (hardcoded and dynamic) 
#
###
def recommendation_alg_tester():
    data_hardcoded = generate_recommendation_data(0) # grabs hardecoded data dict
    data_dyn = generate_recommendation_data(1)       # grabs dyn gen data dict

    results = {}
    numTotalMatches = 0 #number of total matching recommendations
    numTotalRecs = 0 #number of total recommendations made

    #we will base comparisons using the hardcoded data as the referent data

    for subtopic in data_hardcoded:

        recommended_hc = data_hardcoded[subtopic]['related_subtopics'][:10] #grab first 10 recommendations
    
        if subtopic in data_dyn:
            recommended_dy = data_dyn[subtopic]['related_subtopics'][:10]
        else:
            continue #this means that hardocded data had a subtopic not present in topic tree

        #comparisons will be made on the first 10 recommendations, with an emphasis on first 5

        numCompatible = 0 #number of instances where dynamic data matched hardcoded rec data
        for recommendation in recommended_hc:
            if recommendation in recommended_dy:
                numCompatible+=1
                numTotalMatches+=1

            numTotalRecs+=1


        ### init some results! ###
        
        results[subtopic] = {'numCorrect': numCompatible} #number of compatible within a subtopic

        #now focus on first 5 recs for each, for creating the table later
        results[subtopic]['recommendations'] = {'hc': recommended_hc[:5], 'dyn': recommended_dy[:5]}

    results['percentageOfMatching'] = str((round((float(numTotalMatches)/numTotalRecs)*100.0, 2))) + '%'

    return results



def is_content_on_disk(content_id, format="mp4", content_path=None):
    content_path = content_path or settings.CONTENT_ROOT
    content_file = os.path.join(content_path, content_id + ".%s" % format)
    return os.path.isfile(content_file)

