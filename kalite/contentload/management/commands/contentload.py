"""
Utilities for downloading Khan Academy topic tree and
massaging into data and files that we use in KA Lite.
"""
import sys
import json
import os
import importlib
import hashlib

from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.text import slugify

from kalite import topic_tools

from fle_utils.general import ensure_dir

# get the path to an exercise file, so we can check, below, which ones exist
EXERCISE_FILEPATH_TEMPLATE = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s")

def save_cache_file(cache_type, cache_object=None, node_cache=None, data_path=None):

    if cache_object is not None:
        dest_filepath = os.path.join(data_path, cache_type.lower() + "s.json")
        logging.debug("Saving %(cache_type)s to %(dest_filepath)s" % {"cache_type": cache_type, "dest_filepath": dest_filepath})
        with open(dest_filepath, "w") as fp:
            fp.write(json.dumps(cache_object))

def validate_data(topic_tree, node_cache, slug2id_map):
    # Validate related videos
    for exercise in node_cache['Exercise'].values():
        exercise_path = EXERCISE_FILEPATH_TEMPLATE % exercise.get("file_name", "")
        if not os.path.exists(exercise_path) and not exercise.get("uses_assessment_items", False):
            logging.warning("Could not find exercise HTML file: %s\n" % exercise_path)
        for vid_slug in exercise.get("related_video_slugs", []):
            if vid_slug not in slug2id_map or slug2id_map[vid_slug] not in node_cache["Content"]:
                logging.warning("Could not find related video %s in node_cache (from exercise %s)\n" % (vid_slug, exercise["slug"]))

    # Validate all topics have leaves
    for topic in node_cache["Topic"].values():
        if not topic.get("children"):
            logging.warning("Could not find any children for topic %s\n" % (topic["title"]))

    # Validate related content
    for content in node_cache["Content"].values():
        related = content.get("related_content", [])
        if related:
            for cont in related:
                if cont["id"] not in node_cache["Content"] and cont["id"] not in node_cache["Content"] and cont["id"] not in node_cache["Exercise"]:
                    logging.warning("Could not find related content %s in node_cache (from content %s)\n" % (cont["id"], content["slug"]))
        ex = content.get("related_exercise", None)
        if ex:
            if ex["slug"] not in node_cache["Exercise"]:
                logging.warning("Could not find related exercise %s in node_cache (from content %s)\n" % (ex["slug"], content["slug"]))

def scrub_topic_tree(node_cache, channel_data):
    # Now, remove unnecessary values
    for kind_nodes in node_cache.values():
        for node in kind_nodes.values():
            for att in channel_data["temp_ok_atts"]:
                if att in node:
                    if att == "hide" and node["id"] != "root":
                        assert node[att] == False, "All hidden nodes (%s) better be deleted by this point!" % node["id"]
                    if att == "live":
                        assert node[att] == True, "All non-live nodes (%s) better be deleted by this point!" % node["id"]
                    del node[att]


class Command(NoArgsCommand):
    help = """
    **WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches.
    Options:
        [no args] - download from Khan Academy and refresh all files
    """

    option_list = NoArgsCommand.option_list + (
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
        make_option('-d', '--data',
            action='store',
            dest='channel_data',
            default=None,
            help="Add custom path to channel data files"),
    )

    def handle(self, *args, **options):

        channel_name = channel = options["channel"]

        if options["import_files"]:
            channel = "import_channel"

        channel_tools = importlib.import_module("kalite.contentload.management.commands.channels.{channel}".format(channel=channel))

        if options["import_files"]:
            channel_tools.path = options["import_files"]
            if not channel_name or channel_name=="khan":
                channel_name = os.path.basename(options["import_files"])

        if options["channel_data"]:
            channel_tools.channel_data_path = options["channel_data"]

        channel_path = os.path.join(settings.CONTENT_DATA_PATH, slugify(unicode(channel_name)))

        ensure_dir(channel_path)

        channel_id = hashlib.md5(channel_name).hexdigest()

        channel_dict = {
            "id": channel_id,
            "name": channel_name,
            "path": channel_path,
        }

        topic_tree, exercises, assessment_items, content = channel_tools.rebuild_topictree(channel=channel_dict)

        exercise_cache = channel_tools.build_full_cache(exercises, id_key=channel_tools.id_key["Exercise"])
        assessment_item_cache = channel_tools.build_full_cache(assessment_items)
        content_cache = channel_tools.build_full_cache(content)

        node_cache = topic_tools.generate_node_cache(topic_tree)

        node_cache["Exercise"] = exercise_cache
        node_cache["Content"] = content_cache
        node_cache["AssessmentItem"] = assessment_item_cache
        slug2id_map = topic_tools.generate_slug_to_video_id_map(node_cache)

        if channel_tools.channel_data["temp_ok_atts"]:
            scrub_topic_tree(node_cache=node_cache, channel_data=channel_tools.channel_data)

        validate_data(topic_tree, node_cache, slug2id_map)

        # The reason why we catch all errors was that this thing takes
        # around 6 hours to run, and having them error out in the end
        # is kind of a bummer. Since this is meant to just run
        # occasionally on our side (as a hidden feature of KA Lite),
        # it's safe to have this code smell for now.
        try:
            save_cache_file("Topic", cache_object=topic_tree, data_path=channel_path)
            save_cache_file("Exercise", cache_object=exercise_cache, data_path=channel_path)
            save_cache_file("AssessmentItem", cache_object=assessment_item_cache, data_path=channel_path)
            save_cache_file("Content", cache_object=content_cache, data_path=channel_path)

        except Exception as e:

            import IPython; IPython.embed()

        if hasattr(channel_tools, "channel_data_files"):
            channel_tools.channel_data_files(dest=channel_path)

        sys.stdout.write(
            """Downloaded topic_tree data for
            {topics} topics
            {exercises} exercises
            {contents} content files
            {assessments} assessment items
            """.format(
            topics=len(node_cache["Topic"]),
            exercises=len(node_cache["Exercise"]),
            contents=len(node_cache["Content"]),
            assessments=len(node_cache["AssessmentItem"],)
        ))
