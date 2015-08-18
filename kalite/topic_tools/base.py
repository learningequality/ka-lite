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
    return []


CONTENT = None
CACHE_VARS.append("CONTENT")
def get_content_cache(force=False, annotate=False, language=None):

    return {}

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

    return {}

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

def stamp_content_availability(content_list, language="en"):
    # Loop through all content items and put thumbnail urls, content urls,
    # and subtitle urls on the content dictionary, and list all languages
    # that the content is available in.
    try:
        contents_folder = os.listdir(django_settings.CONTENT_ROOT)
    except OSError:
        contents_folder = []

    subtitle_langs = {}

    updates = {}

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

    for content in content_list:
        update = {}
        extra_fields = json.loads(content.extra_fields)

        if content.kind == "Exercise":

            # The central server doesn't have an assessment item database
            if django_settings.CENTRAL_SERVER:
                available = False
            elif extra_fields.get("uses_assessment_items", False):
                available = False
                items = []

                assessment_items = extra_fields.get("all_assessment_items", [])

                for item in assessment_items:
                    item = json.loads(item)
                    if get_assessment_item_data(request=None, assessment_item_id=item.get("id")):
                        items.append(item)
                        available = True
                update["all_assessment_items"] = items
            else:
                exercise_file = extra_fields.get("name") + ".html"

                if language == "en":
                    exercise_template = exercise_file
                else:
                    exercise_template = os.path.join(language, exercise_file)
                    available = exercise_template in exercise_templates
                    update["template"] = exercise_template

            update["available"] = available

        else:
            default_thumbnail = create_thumbnail_url(content.id)
            dubmap = i18n.get_id2oklang_map(content.id)
            if dubmap:
                content_lang = i18n.select_best_available_language(language, available_codes=dubmap.keys()) or ""
                if content_lang:
                    dubbed_id = dubmap.get(content_lang)
                    format = extra_fields.get("format", "")
                    if (dubbed_id + "." + format) in contents_folder:
                        update["available"] = True
                        thumbnail = create_thumbnail_url(dubbed_id) or default_thumbnail
                        update["content_urls"] = {
                            "stream": django_settings.CONTENT_URL + dubmap.get(content_lang) + "." + format,
                            "stream_type": "{kind}/{format}".format(kind=content.kind.lower(), format=format),
                            "thumbnail": thumbnail,
                        }
                    elif django_settings.BACKUP_VIDEO_SOURCE:
                        update["available"] = True
                        update["content_urls"] = {
                            "stream": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format=format),
                            "stream_type": "{kind}/{format}".format(kind=content.kind.lower(), format=format),
                            "thumbnail": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format="png"),
                        }
                    else:
                        update["available"] = False
                else:
                    update["available"] = False
            else:
                update["available"] = False

            # Get list of subtitle language codes currently available
            subtitle_lang_codes = subtitle_langs.get("{id}.srt".format(id=content.id), [])

            # Generate subtitle URLs for any subtitles that do exist for this content item
            subtitle_urls = [{
                "code": lc,
                "url": django_settings.STATIC_URL + "srt/{code}/subtitles/{id}.srt".format(code=lc, id=content.id),
                "name": i18n.get_language_name(lc)
                } for lc in subtitle_lang_codes]

            # Sort all subtitle URLs by language code
            update["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

        with i18n.translate_block(content_lang):
            update["title"] = _(content["title"])
            update["description"] = _(content.description) if content.description else ""

        extra_fields.update(update)

        update = extra_fields

        updates[content.id] = update

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
