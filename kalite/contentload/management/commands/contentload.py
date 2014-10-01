"""
Utilities for downloading Khan Academy topic tree and
massaging into data and files that we use in KA Lite.
"""
import sys
import json
import os
import importlib

from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError

from kalite import topic_tools

# get the path to an exercise file, so we can check, below, which ones exist
EXERCISE_FILEPATH_TEMPLATE = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s.html")

def save_topic_tree(topic_tree=None, node_cache=None, data_path=None):
    assert bool(topic_tree) + bool(node_cache) == 1, "Must specify either topic_tree or node_cache parameter"
    # Dump the topic tree (again)
    topic_tree = topic_tree or node_cache["Topic"]["root"]

    dest_filepath = os.path.join(data_path, topic_tools.TOPICS_FILEPATH)
    logging.debug("Saving topic tree to %s" % dest_filepath)
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(dict(topic_tree)))


def save_cache_file(cache_type, cache_object=None, node_cache=None, data_path=None):
    
    cache_object = cache_object or node_cache[cache_object]

    dest_filepath = os.path.join(data_path, cache_type.lower() + "s.json")
    logging.debug("Saving %(cache_type)s to %(dest_filepath)s" % {"cache_type": cache_type, "dest_filepath": dest_filepath})
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(cache_object))

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



class Command(BaseCommand):
    help = """**WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches from Khan Academy.
    Options:
        [no args] - download from Khan Academy and refresh all files
    """

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-c', '--channel',
            dest='channel',
            default="khan",
            help='Create content files for a channel'),
        make_option('-i', '--import',
            action='store',
            dest='import_files',
            default=None,
            help="Import a file structure as a topic tree and move over the appropriate content"),
    )

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Unknown argument list: %s" % args)

        channel = options["channel"]

        if options["import_files"]:
            channel = "import_channel"

        channel_tools = importlib.import_module("kalite.contentload.management.commands.channels." + channel)

        if options["import_files"]:
            channel_tools.path = options["import_files"]

        channel_path = os.path.join(settings.CONTENT_DATA_PATH, channel)

        topic_tree, exercises, videos, assessment_items, content = channel_tools.rebuild_topictree()

        exercise_cache = channel_tools.build_full_cache(exercises, id_key=channel_tools.id_key["Exercise"])
        video_cache = channel_tools.build_full_cache(videos, id_key=channel_tools.id_key["Video"])
        assessment_item_cache = channel_tools.build_full_cache(assessment_items)
        content = channel_tools.build_full_cache(content)
        
        node_cache = topic_tools.generate_node_cache(topic_tree)
        
        node_cache["Exercise"] = channel_tools.exercise_cache
        node_cache["Video"] = channel_tools.video_cache
        slug2id_map = topic_tools.generate_slug_to_video_id_map(node_cache)
        
        scrub_topic_tree(node_cache=node_cache)

        validate_data(topic_tree, node_cache, slug2id_map)

        level_cache = channel_tools.recurse_topic_tree_to_create_hierarchy(topic_tree)

        save_topic_tree(topic_tree, data_path=channel_path)
        save_cache_file("Exercise", cache_object=exercise_cache, data_path=channel_path)
        save_cache_file("Video", cache_object=video_cache, data_path=channel_path)
        save_cache_file("AssessmentItem", cache_object=assessment_item_cache, data_path=channel_path)
        save_cache_file("Content", cache_object=content, data_path=channel_path)
        for level in channel_tools.hierarchy:
            save_cache_file("Map_" + level, cache_object=level_cache[level], data_path=channel_path)

        sys.stdout.write("Downloaded topic_tree data for %d topics, %d videos, %d exercises\n" % (
            len(node_cache["Topic"]),
            len(node_cache["Video"]),
            len(node_cache["Exercise"]),
        ))
