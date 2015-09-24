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

from django.conf import settings as django_settings
logging = django_settings.LOG

from django.contrib import messages
from django.db import DatabaseError
from django.utils.translation import gettext as _

from fle_utils.general import softload_json, json_ascii_decoder
from kalite import i18n

from . import models as main_models
from . import settings


CACHE_VARS = []


if not os.path.exists(django_settings.CHANNEL_DATA_PATH):
    logging.warning("Channel {channel} does not exist.".format(channel=django_settings.CHANNEL))


def cache_file_path(basename):
    """Consistently return path for a cache filename. This path has to be
    writable for the user running kalite."""
    assert "/" not in basename, "Please use a valid filename"
    cache_dir = os.path.join(django_settings.USER_DATA_ROOT, 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return os.path.join(cache_dir, basename)


# Globals that can be filled
TOPICS = None
CACHE_VARS.append("TOPICS")
CNT = 0
def get_topic_tree(force=False, annotate=False, channel=None, language=None, parent=None):

    # Hardcode the Brazilian Portuguese mapping that only the central server knows about
    # TODO(jamalex): BURN IT ALL DOWN!
    if language == "pt-BR":
        language = "pt"

    if not channel:
        channel = django_settings.CHANNEL

    if not language:
        language = django_settings.LANGUAGE_CODE

    global TOPICS
    if not TOPICS:
        TOPICS = {}
    if TOPICS.get(channel) is None:
        TOPICS[channel] = {}

    if annotate or TOPICS.get(channel, {}).get(language) is None:
        cached_topics = None
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            cached_topics = softload_json(
                cache_file_path("topic_{0}_{1}.json".format(channel, language)),
                logger=logging.debug,
                raises=False
            )
        if cached_topics:
            TOPICS[channel][language] = cached_topics
            annotate = False
        else:
            topics = softload_json(settings.TOPICS_FILEPATHS.get(channel), logger=logging.debug, raises=False)
            # Just loaded from disk, so have to restamp.
            annotate = True

    if annotate:
        flat_topic_tree = []

        # Loop through all the nodes in the topic tree
        # and cross reference with the content_cache to check availability.
        content_cache = get_content_cache(language=language)
        exercise_cache = get_exercise_cache(language=language)

        def recurse_nodes(node, parent=""):

            node["parent"] = parent

            node.pop("child_data", None)

            child_availability = []

            child_ids = [child.get("id") for child in node.get("children", [])]

            # Do the recursion
            for child in node.get("children", []):
                recurse_nodes(child, node.get("id"))
                child_availability.append(child.get("available", False))

            if child_ids:
                node["children"] = child_ids

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

            flat_topic_tree.append(node)

        recurse_nodes(topics)

        TOPICS[channel][language] = flat_topic_tree

        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
            try:
                with open(cache_file_path("topic_{0}_{1}.json".format(channel, language)), "w") as f:
                    json.dump(TOPICS[channel][language], f)
            except IOError as e:
                logging.warn("Annotated topic cache file failed in saving with error {e}".format(e=e))

    if parent:
        return filter(lambda x: x.get("parent") == parent, TOPICS[channel][language])
    else:
        return TOPICS[channel][language]


NODE_CACHE = None
CACHE_VARS.append("NODE_CACHE")
def get_node_cache(node_type=None, force=False, language=None):

    if not language:
        language = django_settings.LANGUAGE_CODE

    global NODE_CACHE
    if NODE_CACHE is None or force:
        NODE_CACHE = generate_node_cache()
    if node_type is None:
        return NODE_CACHE
    else:
        return NODE_CACHE[node_type]

EXERCISES = None
CACHE_VARS.append("EXERCISES")
def get_exercise_cache(force=False, language=None):

    if not language:
        language = django_settings.LANGUAGE_CODE

    global EXERCISES
    if EXERCISES is None:
        EXERCISES = {}
    if EXERCISES.get(language) is None:
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            exercises = softload_json(
                cache_file_path("exercises_{0}.json".format(language)),
                logger=logging.debug,
                raises=False
            )
            if exercises:
                EXERCISES[language] = exercises
                return EXERCISES[language]
        EXERCISES[language] = softload_json(settings.EXERCISES_FILEPATH, logger=logging.debug, raises=False)

        # English-language exercises live in application space, translations in user space
        if language == "en":
            exercise_root = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
        else:
            exercise_root = i18n.get_localized_exercise_dirpath(language)
        if os.path.exists(exercise_root):
            try:
                exercise_templates = os.listdir(exercise_root)
            except OSError:
                exercise_templates = []
        else:
            exercise_templates = []

        for exercise in EXERCISES[language].values():
            exercise_file = exercise["name"] + ".html"
            exercise_template = exercise_file
            exercise_lang = "en"

            # The central server doesn't have an assessment item database
            if django_settings.CENTRAL_SERVER:
                available = False
            elif exercise.get("uses_assessment_items", False):
                available = False
                items = []
                for item in exercise.get("all_assessment_items", []):
                    item = json.loads(item)
                    if get_assessment_item_data(request=None, assessment_item_id=item.get("id")):
                        items.append(item)
                        available = True
                exercise["all_assessment_items"] = items
            else:
                available = exercise_template in exercise_templates

                # Get the language codes for exercise templates that exist
                # Try to minimize the number of os.path.exists calls (since they're a bottleneck) by using the same
                # precedence rules in i18n.select_best_available_languages
                available_langs = set(["en"] + [language] * available)
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
                with open(cache_file_path("exercises_{0}.json".format(language)), "w") as f:
                    json.dump(EXERCISES[language], f)
            except IOError as e:
                logging.warn("Annotated exercise cache file failed in saving with error {e}".format(e=e))

    return EXERCISES[language]


LEAFED_TOPICS = None
CACHE_VARS.append("LEAFED_TOPICS")
def get_leafed_topics(force=False, language=None):

    if not language:
        language = django_settings.LANGUAGE_CODE

    global LEAFED_TOPICS
    if LEAFED_TOPICS is None or force:
        topic_cache = get_node_cache(language=language)["Topic"]
        LEAFED_TOPICS = [topic for topic in topic_cache.values() if [child for child in topic.get("children", []) if topic_cache.get(child, {}).get("kind") != "Topic"]]
    return LEAFED_TOPICS

def create_thumbnail_url(thumbnail):
    if is_content_on_disk(thumbnail, "png"):
        return django_settings.CONTENT_URL + thumbnail + ".png"
    elif is_content_on_disk(thumbnail, "jpg"):
        return django_settings.CONTENT_URL + thumbnail + ".jpg"
    return None

CONTENT = None
CACHE_VARS.append("CONTENT")
def get_content_cache(force=False, annotate=False, language=None):

    if not language:
        language = django_settings.LANGUAGE_CODE

    global CONTENT

    if CONTENT is None:
        CONTENT = {}

    if CONTENT.get(language) is None:
        content = None
        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP and not force:
            content = softload_json(
                cache_file_path("content_{0}.json".format(language)),
                logger=logging.debug,
                raises=False
            )
        if content:
            CONTENT[language] = content
            return CONTENT[language]
        else:
            CONTENT[language] = softload_json(settings.CONTENT_FILEPATH, logger=logging.debug, raises=False)
            annotate = True

    if annotate:

        # Loop through all content items and put thumbnail urls, content urls,
        # and subtitle urls on the content dictionary, and list all languages
        # that the content is available in.
        try:
            contents_folder = os.listdir(django_settings.CONTENT_ROOT)
        except OSError:
            contents_folder = []

        subtitle_langs = {}

        if os.path.exists(i18n.get_srt_path()):
            for (dirpath, dirnames, filenames) in os.walk(i18n.get_srt_path()):
                # Only both looking at files that are inside a 'subtitles' directory
                if os.path.basename(dirpath) == "subtitles":
                    lc = os.path.basename(os.path.dirname(dirpath))
                    for filename in filenames:
                        if filename in subtitle_langs:
                            subtitle_langs[filename].append(lc)
                        else:
                            subtitle_langs[filename] = [lc]

        for content in CONTENT[language].values():
            default_thumbnail = create_thumbnail_url(content.get("id"))
            dubmap = i18n.get_id2oklang_map(content.get("id"))
            if dubmap:
                content_lang = i18n.select_best_available_language(language, available_codes=dubmap.keys()) or ""
                if content_lang:
                    dubbed_id = dubmap.get(content_lang)
                    format = content.get("format", "")
                    if (dubbed_id + "." + format) in contents_folder:
                        content["available"] = True
                        thumbnail = create_thumbnail_url(dubbed_id) or default_thumbnail
                        content["content_urls"] = {
                            "stream": django_settings.CONTENT_URL + dubmap.get(content_lang) + "." + format,
                            "stream_type": "{kind}/{format}".format(kind=content.get("kind", "").lower(), format=format),
                            "thumbnail": thumbnail,
                        }
                    elif django_settings.BACKUP_VIDEO_SOURCE:
                        content["available"] = True
                        content["content_urls"] = {
                            "stream": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format=format),
                            "stream_type": "{kind}/{format}".format(kind=content.get("kind", "").lower(), format=format),
                            "thumbnail": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format="png"),
                        }
                    else:
                        content["available"] = False
                else:
                    content["available"] = False
            else:
                content["available"] = False

            # Get list of subtitle language codes currently available
            subtitle_lang_codes = subtitle_langs.get("{id}.srt".format(id=content.get("id")), [])

            # Generate subtitle URLs for any subtitles that do exist for this content item
            subtitle_urls = [{
                "code": lc,
                "url": django_settings.STATIC_URL + "srt/{code}/subtitles/{id}.srt".format(code=lc, id=content.get("id")),
                "name": i18n.get_language_name(lc)
                } for lc in subtitle_lang_codes]

            # Sort all subtitle URLs by language code
            content["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

            with i18n.translate_block(content_lang):
                content["selected_language"] = content_lang
                content["title"] = _(content["title"])
                content["description"] = _(content.get("description")) if content.get("description") else ""

        if settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP:
            try:
                with open(cache_file_path("content_{0}.json".format(language)), "w") as f:
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


def generate_node_cache(topictree=None, language=None):
    """
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Content nodes.
    """

    if not language:
        language = django_settings.LANGUAGE_CODE

    if not topictree:
        topictree = get_topic_tree(language=language)
    node_cache = {}

    node_cache["Topic"] = dict([(node.get("id"), node) for node in topictree])

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
    Returns all leaves of type leaf_type, at all levels of the tree.

    If leaf_type is None, returns all child nodes of all types and levels.
    """
    if not topic_node:
        topic_node = get_node_cache()["Topic"].get("root")
    leaves = [topic for topic in get_topic_tree() if (not leaf_type or topic.get("kind") == leaf_type) and (topic_node.get("path") in topic.get("path"))]

    return leaves


def get_topic_leaves(topic_id=None, leaf_type=None):
    """Given a topic (identified by topic_id ), return all descendent leaf nodes"""

    topic_node = get_node_cache('Topic').get(topic_id, None)

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

    return exercise


def get_assessment_item_data(request, assessment_item_id=None):
    try:
        assessment_item = main_models.AssessmentItem.objects.get(id=assessment_item_id)
    except main_models.AssessmentItem.DoesNotExist:
        return None
    except DatabaseError:
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

    language = request.language

    # Hardcode the Brazilian Portuguese mapping that only the central server knows about
    # TODO(jamalex): BURN IT ALL DOWN!
    if language == "pt-BR":
        language = "pt"

    content_cache = get_content_cache(language=language)
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

def get_topic_data(request, topic_id=None):
    topic_cache = get_node_cache(node_type='Topic', language=request.language)
    topic = topic_cache.get(topic_id, None)

    return topic

def video_dict_by_video_id(node_cache=None):
    # TODO (aron): Add i18n by varying the language of the topic tree here
    topictree = node_cache if node_cache else get_node_cache()

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
    content_path = content_path or django_settings.CONTENT_ROOT
    content_file = os.path.join(content_path, content_id + ".%s" % format)
    return os.path.isfile(content_file)
