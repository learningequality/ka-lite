"""
TODO: NOTHING SHOULD BE HERE! It's prohibiting the import of other topic_tools.xxx
modules at load time because it has so many preconditions for loading.

For now, it means that topic_tools.settings has been copied over to kalite.settings


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

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.utils.translation import gettext as _

from fle_utils.general import softload_json, json_ascii_decoder
from kalite import i18n

from kalite.main import models as main_models

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
        TEMPLATE_FILE_PATH = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s")
        for exercise in EXERCISES[language].values():
            exercise_file = exercise["name"] + ".html"
            exercise_template = exercise_file
            exercise_lang = "en"

            if exercise.get("uses_assessment_items", False):
                available = False
                items = []
                for item in exercise.get("all_assessment_items","[]"):
                    item = json.loads(item)
                    if get_assessment_item_data(request=None, assessment_item_id=item.get("id")):
                        items.append(item)
                        available = True
                exercise["all_assessment_items"] = items
            else:
                available = os.path.isfile(TEMPLATE_FILE_PATH % exercise_template)

                # Get the language codes for exercise templates that exist
                # Try to minimize the number of os.path.exists calls (since they're a bottleneck) by using the same
                # precedence rules in i18n.select_best_available_languages
                available_langs = [lang_code for lang_code in exercise_templates if language in lang_code or lang_code == settings.LANGUAGE_CODE]
                available_langs = [lang_code for lang_code in available_langs if os.path.exists(os.path.join(exercise_root, lang_code, exercise_file))]
                available_langs = set(["en"] + available_langs)
                # Return the best available exercise template
                exercise_lang = i18n.select_best_available_language(language, available_codes=available_langs)

            if exercise_lang == "en":
                exercise_template = exercise_file
            else:
                exercise_template = os.path.join(exercise_lang, exercise_file)

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
                content["description"] = _(content.get("description")) if content.get("description") else ""

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
    try:
        assessment_item = main_models.AssessmentItem.objects.get(id=assessment_item_id)
    except main_models.AssessmentItem.DoesNotExist:
        return None

    try:
        item_data = json.loads(assessment_item.item_data, object_hook=json_ascii_decoder)
        item_data = smart_translate_item_data(item_data)
        item_data = json.dumps(item_data)
    except KeyError as e:
        logging.error("Assessment item did not have the expected key %s. Assessment item: \n %s" % (e, assessment_item))

    #  Expects a dict
    return {
        "id": assessment_item.id,
        "item_data": item_data,
        "author_names": assessment_item.author_names,
    }


def smart_translate_item_data(item_data):
    """Auto translate the content fields of a given assessment item data.

    An assessment item doesn't have the same fields; they change
    depending on the question. Instead of manually specifying the
    fields to translate, this function loops over all fields of
    item_data and translates only the content field.

    """
    # just translate strings immediately
    if isinstance(item_data, basestring):
        return _(item_data)

    elif isinstance(item_data, list):
        return map(smart_translate_item_data, item_data)

    elif isinstance(item_data, dict):
        if 'content' in item_data:
            item_data['content'] = _(item_data['content']) if item_data['content'] else ""

        for field, field_data in item_data.iteritems():
            if isinstance(field_data, dict):
                item_data[field] = smart_translate_item_data(field_data)
            elif isinstance(field_data, list):
                item_data[field] = map(smart_translate_item_data, field_data)

        return item_data



def get_content_data(request, content_id=None):

    content_cache = get_content_cache(language=request.language)
    content = content_cache.get(content_id, None)

    if not content:
        return None

    if not content.get("content_urls", None):
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this content in the topic tree
            messages.warning(request, _("This content was not found! You can download it by going to the Manage > Videos page."))
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


def is_content_on_disk(content_id, format="mp4", content_path=None):
    content_path = content_path or settings.CONTENT_ROOT
    content_file = os.path.join(content_path, content_id + ".%s" % format)
    return os.path.isfile(content_file)
