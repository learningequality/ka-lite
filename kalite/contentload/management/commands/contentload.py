"""
Utilities for downloading Khan Academy topic tree and
massaging into data and files that we use in KA Lite.
"""
import copy
import datetime
import json
import os
import requests
import shutil
import sys
import time

from khan_api_python.api_models import Khan, APIError
from math import ceil, log, exp  # needed for basepoints calculation
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError

from ... import KHANLOAD_CACHE_DIR, kind_slugs
from fle_utils.general import datediff
from kalite import topic_tools


# get the path to an exercise file, so we can check, below, which ones exist
EXERCISE_FILEPATH_TEMPLATE = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s.html")

slug_key = {
    "Topic": "node_slug",
    "Video": "readable_id",
    "Exercise": "name",
    "AssessmentItem": "id",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
    "AssessmentItem": "name"
}

id_key = {
    "Topic": "node_slug",
    "Video": "youtube_id",
    "Exercise": "name",
    "AssessmentItem": "id"
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src", "child_data", "render_type", "path", "slug"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id", "y_pos", "x_pos", "in_knowledge_map", "path", "slug"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "y_pos", "x_pos", "in_knowledge_map", "all_assessment_items", "uses_assessment_items", "path", "slug"],
    "AssessmentItem": ["kind", "name", "item_data", "tags", "author_names", "sha", "id"]
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "duration", "youtube_id", "readable_id", "id", "y_pos", "x_pos", "path", "slug"],
    "Exercise": ["kind", "description", "title", "display_name", "name", "id", "y_pos", "x_pos", "path", "slug"]
}

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res", "MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "cs", "cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math", "cc-seventh-grade-math", "cc-eighth-grade-math", "hour-of-code"]

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = ["icon_src", u'topic_page_url', u'hide', "live", "node_slug", "extended_slug"]


def whitewash_node_data(node, path="", ancestor_ids=[]):
    """
    Utility function to convert nodes into the format used by KA Lite.
    Extracted from other functions so as to be reused by both the denormed
    and fully inflated exercise and video nodes.
    """

    kind = node.get("kind", None)

    if not kind:
        return node

    node["x_pos"] = node.get("x_pos", 0) or node.get("h_position", 0)
    node["y_pos"] = node.get("y_pos", 0) or node.get("v_position", 0)

    # Only keep key data we can use
    for key in node.keys():
        if key not in attribute_whitelists[kind]:
            del node[key]

    # Fix up data
    if slug_key[kind] not in node:
        # logging.warn("Could not find expected slug key (%s) on node: %s" % (slug_key[kind], node))
        node[slug_key[kind]] = node["id"]  # put it SOMEWHERE.

    node["slug"] = node[slug_key[kind]] if node[slug_key[kind]] != "root" else ""
    node["id"] = node[id_key[kind]]  # these used to be the same; now not. Easier if they stay the same (issue #233)

    node["path"] = path + kind_slugs[kind] + node["slug"] + "/"
    node["title"] = (node[title_key[kind]] or "").strip()

    # Add some attribute that should have been on there to start with.
    node["parent_id"] = ancestor_ids[-1] if ancestor_ids else None
    node["ancestor_ids"] = ancestor_ids

    if kind == "Video":
        # TODO: map new videos into old videos; for now, this will do nothing.
        node["video_id"] = node["youtube_id"]

    elif kind == "Exercise":
        # For each exercise, need to set the exercise_id
        #   get related videos
        #   and compute base points
        node["exercise_id"] = node["slug"]

        # compute base points
        # Minimum points per exercise: 5
        node["basepoints"] = ceil(7 * log(max(exp(5./7), node.get("seconds_per_fast_problem", 0))));

    return node

def rebuild_topictree(remove_unknown_exercises=False, remove_disabled_topics=True):
    """Downloads topictree (and supporting) data from Khan Academy and uses it to
    rebuild the KA Lite topictree cache (topics.json).
    """

    khan = Khan()

    topic_tree = khan.get_topic_tree()

    exercises = khan.get_exercises()

    exercise_lookup = {exercise["id"]: exercise for exercise in exercises}

    videos = khan.get_videos()

    video_lookup = {video["id"]: video for video in videos}

    assessment_items = []

    for exercise in exercises:
        for assessment_item in exercise.all_assessment_items:
            assessment_items.append(khan.get_assessment_item(assessment_item["id"]))

    #Do Something Terrible Today

    def recurse_nodes(node, path="", ancestor_ids=[]):
        """
        Internal function for recursing over the topic tree, marking relevant metadata,
        and removing undesired attributes and children.
        """

        kind = node["kind"]

        node = whitewash_node_data(node, path, ancestor_ids)

        if kind == "Exercise" or kind == "Video":
            for key in node.keys():
                if key not in denormed_attribute_list[kind]:
                    del node[key]

        # Loop through children, remove exercises and videos to reintroduce denormed data
        children_to_delete = []
        child_kinds = set()
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)

            if child_kind=="Video" or child_kind=="Exercise":
                children_to_delete.append(i)

        for i in reversed(children_to_delete):
            # Reversing means that earlier indices are unaffected by deletion of later ones.
            del node["children"][i]

        # Loop through child_data to populate children with denormed data of exercises and videos.
        for child_datum in node.get("child_data", []):
            try:
                if child_datum["kind"] == "Exercise":
                    child_denormed_data = exercise_lookup[str(child_datum["id"])]
                elif child_datum["kind"] == "Video":
                    child_denormed_data = video_lookup[str(child_datum["id"])]
                else:
                    child_denormed_data = None
                if child_denormed_data:
                    node["children"].append(copy.deepcopy(dict(child_denormed_data)))
            except KeyError as e:
                logging.warn("%(kind)s %(id)s does not exist in lookup table" % child_datum)


        # Recurse through children, remove any blacklisted items
        children_to_delete = []
        child_kinds = set()
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)

            # Blacklisted--remove
            if child_kind in kind_blacklist:
                children_to_delete.append(i)
                continue
            elif child[slug_key[child_kind]] in slug_blacklist:
                children_to_delete.append(i)
                continue
            elif not child.get("live", True) and remove_disabled_topics:  # node is not live
                logging.debug("Removing non-live child: %s" % child[slug_key[child_kind]])
                children_to_delete.append(i)
                continue
            elif child.get("hide", False) and remove_disabled_topics:  # node is hidden. Note that root is hidden, and we're implicitly skipping that.
                children_to_delete.append(i)
                logging.debug("Removing hidden child: %s" % child[slug_key[child_kind]])
                continue
            elif child_kind == "Video" and set(["mp4", "png"]) - set(child.get("download_urls", {}).keys()):
                # for now, since we expect the missing videos to be filled in soon,
                #   we won't remove these nodes
                sys.stderr.write("WARNING: No download link for video: %s\n" % child["youtube_id"])
                children_to_delete.append(i)
                continue

            child_kinds = child_kinds.union(set([child_kind]))
            child_kinds = child_kinds.union(recurse_nodes(child, path=node["path"], ancestor_ids=ancestor_ids + [node["id"]]))

        # Delete those marked for completion
        for i in reversed(children_to_delete):
            # Reversing means that earlier indices are unaffected by deletion of later ones.
            del node["children"][i]

        # Mark on topics whether they contain Videos, Exercises, or both
        if kind == "Topic":
            node["contains"] = list(child_kinds)

        return child_kinds
    recurse_nodes(topic_tree)

    def recurse_nodes_to_remove_childless_nodes(node):
        """
        When we remove exercises, we remove dead-end topics.
        Khan just sends us dead-end topics, too.
        Let's remove those too.
        """
        children_to_delete = []
        for ci, child in enumerate(node.get("children", [])):
            # Mark all unrecognized exercises for deletion
            if child["kind"] != "Topic":
                continue

            recurse_nodes_to_remove_childless_nodes(child)

            if not child.get("children"):
                children_to_delete.append(ci)
                logging.warn("Removing KA childless topic: %s" % child["slug"])

        for ci in reversed(children_to_delete):
            del node["children"][ci]
    recurse_nodes_to_remove_childless_nodes(topic_tree)

    def recurse_nodes_to_add_position_data(node):
        """
        Only execises have position data associated with them.
        To get position data for higher level topics, averaging of
        lower level positions can be used to give a center of mass.
        """
        if node["kind"] == "Topic":
            x_pos = []
            y_pos = []
            videos = []
            for child in node.get("children", []):
                if not (child.get("x_pos", 0) and child.get("y_pos", 0)):
                    recurse_nodes_to_add_position_data(child)
                if child.get("x_pos", 0) and child.get("y_pos", 0):
                    x_pos.append(child["x_pos"])
                    y_pos.append(child["y_pos"])
                elif child["kind"] == "Video":
                    videos.append(child)
            if len(x_pos) and len(y_pos):
                node["x_pos"] = sum(x_pos)/float(len(x_pos))
                node["y_pos"] = sum(y_pos)/float(len(y_pos))
                for i, video in enumerate(videos):
                    video["x_pos"] = min(x_pos) + (max(x_pos) - min(x_pos))*i/float(len(videos))
                    video["y_pos"] = min(y_pos) + (max(y_pos) - min(y_pos))*i/float(len(videos))

    recurse_nodes_to_add_position_data(topic_tree)

    return topic_tree, exercises, videos, assessment_items

def build_full_cache(items, id_key="id"):
    """
    Uses list of items retrieved from Khan Academy API to
    create an item cache with fleshed out meta-data.
    """
    for item in items:
        for attribute in item._API_attributes:
            try:
                dummy_variable_to_force_fetch = item.__getattr__(attribute)
                if isinstance(item[attribute], list):
                    for subitem in item[attribute]:
                        if isinstance(subitem, dict):
                            if subitem.has_key("kind"):
                                subitem = whitewash_node_data(
                                    {key: value for key, value in subitem.items()
                                    if key in denormed_attribute_list[subitem["kind"]]})
                elif isinstance(item[attribute], dict):
                    if item[attribute].has_key("kind"):
                        item[attribute] = whitewash_node_data(
                            {key: value for key, value in item.attribute.items()
                            if key in denormed_attribute_list[item[attribute]["kind"]]})
            except APIError as e:
                del item[attribute]
    return {item["id"]: whitewash_node_data(item) for item in items}


def validate_data(topic_tree, node_cache, slug2id_map):
    # Validate related videos
    for exercise in node_cache['Exercise'].values():
        exercise_path = EXERCISE_FILEPATH_TEMPLATE % exercise["slug"]
        if not os.path.exists(exercise_path) and not exercise.get("uses_assessment_items", False):
            sys.stderr.write("Could not find exercise HTML file: %s\n" % exercise_path)
        for vid_slug in exercise.get("related_video_slugs", []):
            if vid_slug not in slug2id_map or slug2id_map[vid_slug] not in node_cache["Video"]:
                sys.stderr.write("Could not find related video %s in node_cache (from exercise %s)\n" % (vid_slug, exercise["slug"]))

    # Validate related exercises
    for video in node_cache["Video"].values():
        ex = video.get("related_exercise", None)
        if ex:
            if ex["slug"] not in node_cache["Exercise"]:
                sys.stderr.write("Could not find related exercise %s in node_cache (from video %s)\n" % (ex["slug"], video["slug"]))

    # Validate all topics have leaves
    for topic in node_cache["Topic"].values():
        if not topic_tools.get_topic_by_path(topic["path"], root_node=topic_tree).get("children"):
            sys.stderr.write("Could not find any children for topic %s\n" % (topic["path"]))

def scrub_topic_tree(node_cache):
    # Now, remove unnecessary values
    for kind_nodes in node_cache.values():
        for node in kind_nodes.values():
            for att in temp_ok_atts:
                if att in node:
                    if att == "hide" and node["id"] != "root":
                        assert node[att] == False, "All hidden nodes (%s) better be deleted by this point!" % node["id"]
                    if att == "live":
                        assert node[att] == True, "All non-live nodes (%s) better be deleted by this point!" % node["id"]
                    del node[att]



def save_topic_tree(topic_tree=None, node_cache=None, data_path=os.path.join(settings.PROJECT_PATH, "static", "data")):
    assert bool(topic_tree) + bool(node_cache) == 1, "Must specify either topic_tree or node_cache parameter"
    # Dump the topic tree (again)
    topic_tree = topic_tree or node_cache["Topic"]["root"]

    dest_filepath = os.path.join(data_path, topic_tools.TOPICS_FILEPATH)
    logging.debug("Saving topic tree to %s" % dest_filepath)
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(dict(topic_tree)))


def save_cache_file(cache_type, cache_object=None, node_cache=None, data_path=settings.KHAN_DATA_PATH):
    
    cache_object = cache_object or node_cache[cache_object]

    dest_filepath = os.path.join(data_path, cache_type.lower() + "s.json")
    logging.debug("Saving %(cache_type)s to %(dest_filepath)s" % {"cache_type": cache_type, "dest_filepath": dest_filepath})
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(cache_object))

def recurse_topic_tree_to_create_DSTT_hierarchy(node, level_cache={}):
    hierarchy = ["Domain", "Subject", "Topic", "Tutorial"]
    if not level_cache:
        for hier in hierarchy:
            level_cache[hier] = []
    render_type = node.get("render_type", "")
    if render_type in hierarchy:
        node_copy = copy.deepcopy(dict(node))
        for child in node_copy.get("children", []):
            if child.has_key("children"):
                del child["children"]
        level_cache[render_type].append(node_copy)
    for child in node.get("children", []):
        recurse_topic_tree_to_create_DSTT_hierarchy(child, level_cache)
    return level_cache



class Command(BaseCommand):
    help = """**WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches from Khan Academy.
    Options:
        [no args] - download from Khan Academy and refresh all files
    """

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-i', '--force-icons',
            action='store_true',
            dest='force_icons',
            default=False,
            help='Force the download of each icon'),
        make_option('-k', '--keep-new-exercises',
            action='store_true',
            dest='keep_new_exercises',
            default=False,
            help="Keep data on new exercises (if not specified, these are stripped out, as we don't have code to download/use them)"),
    )

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Unknown argument list: %s" % args)

        # TODO(bcipolli)
        # Make remove_unknown_exercises and force_icons into command-line arguments
        topic_tree, exercises, videos, assessment_items = rebuild_topictree()

        exercise_cache = build_full_cache(exercises, id_key=id_key["Exercise"])
        video_cache = build_full_cache(videos, id_key=id_key["Video"])
        assessment_item_cache = build_full_cache(assessment_items)
        
        node_cache = topic_tools.generate_node_cache(topic_tree)
        
        node_cache["Exercise"] = exercise_cache
        node_cache["Video"] = video_cache
        slug2id_map = topic_tools.generate_slug_to_video_id_map(node_cache)
        
        # Disabled until we revamp it based on the current KA API.
        # h_position and v_position are available on each exercise now.
        # If not on the topic_tree, then here: http://api-explorer.khanacademy.org/api/v1/playlists/topic_slug/exercises
        # rebuild_knowledge_map(topic_tree, node_cache, force_icons=options["force_icons"])

        scrub_topic_tree(node_cache=node_cache)

        validate_data(topic_tree, node_cache, slug2id_map)

        level_cache = recurse_topic_tree_to_create_DSTT_hierarchy(topic_tree)

        save_topic_tree(topic_tree)
        save_cache_file("Exercise", cache_object=exercise_cache)
        save_cache_file("Video", cache_object=video_cache)
        save_cache_file("AssessmentItem", cache_object=assessment_item_cache)
        save_cache_file("Map_Domain", cache_object=level_cache["Domain"])
        save_cache_file("Map_Subject", cache_object=level_cache["Subject"])
        save_cache_file("Map_Topic", cache_object=level_cache["Topic"])
        save_cache_file("Map_Tutorial", cache_object=level_cache["Tutorial"])

        sys.stdout.write("Downloaded topic_tree data for %d topics, %d videos, %d exercises\n" % (
            len(node_cache["Topic"]),
            len(node_cache["Video"]),
            len(node_cache["Exercise"]),
        ))
