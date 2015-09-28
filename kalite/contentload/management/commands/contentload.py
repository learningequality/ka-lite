"""
Utilities for downloading Khan Academy topic tree and
massaging into data and files that we use in KA Lite.
"""
import json
import os
import importlib
import hashlib

from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from fle_utils.general import ensure_dir

def save_cache_file(cache_type, cache_object=None, node_cache=None, data_path=None):

    if cache_object is not None:
        dest_filepath = os.path.join(data_path, cache_type.lower() + "s.json")
        logging.debug("Saving %(cache_type)s to %(dest_filepath)s" % {"cache_type": cache_type, "dest_filepath": dest_filepath})
        with open(dest_filepath, "w") as fp:
            fp.write(json.dumps(cache_object))


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


def topic_tree_id_catalog(topic_tree):
    """
    Takes the topic tree and returns a dictionary with the ids of all nodes in the tree
    This is for use in removing items from caches that are not in the topic tree
    """
    ids = set()
    def recurse_nodes(node):
        ids.add(node.get("id"))

        for child in node.get("children", []):
            recurse_nodes(child)
    recurse_nodes(topic_tree)

    return ids


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
            help='Create content files for a channel. Value of argument is the name of the channel.'),
        make_option('-i', '--import',
            action='store',
            dest='import_files',
            default=None,
            help=("Import a file structure as a topic tree and move over the appropriate content.\n"
                  "The value of this argument is the path to the content to be imported."
                  "Do not include a trailing slash.")),
        make_option('-d', '--data',
            action='store',
            dest='channel_data',
            default=None,
            help=("Add custom path to channel data files.\n"
                  "Value of the argument is path to directory containing channel metadata file(s?)."
                  "Do not include trailing slash.")),
    )

    def handle(self, *args, **options):

        channel_name = channel = options["channel"]

        if options["import_files"]:
            channel = "import_channel"

        channel_tools = importlib.import_module("kalite.contentload.management.commands.channels.{channel}".format(channel=channel))

        if options["import_files"]:
            # Specifies where the files are coming from
            channel_tools.path = options["import_files"]
            if not channel_name or channel_name=="khan":
                channel_name = os.path.basename(options["import_files"])

        assert channel_name, "Channel name must not be empty. Make sure you used correct arguments."

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

        ids = topic_tree_id_catalog(topic_tree)

        exercise_cache = channel_tools.build_full_cache(exercises, id_key=channel_tools.id_key["Exercise"], ids=ids)
        assessment_item_cache = channel_tools.build_full_cache(assessment_items)
        content_cache = channel_tools.build_full_cache(content, ids=ids)

        node_cache = {}

        node_cache["Exercise"] = exercise_cache
        node_cache["Content"] = content_cache
        node_cache["AssessmentItem"] = assessment_item_cache

        if channel_tools.channel_data["temp_ok_atts"]:
            scrub_topic_tree(node_cache=node_cache, channel_data=channel_tools.channel_data)

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

        logging.info(
            """Downloaded topic_tree data for
            {exercises} exercises
            {contents} content files
            {assessments} assessment items
            """.format(
            exercises=len(node_cache["Exercise"]),
            contents=len(node_cache["Content"]),
            assessments=len(node_cache["AssessmentItem"]),
        ))
