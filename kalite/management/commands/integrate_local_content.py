"""
Command to integrate 3rd party (non-Khan Academy) content
into the topic tree and content directory.
"""

import glob
import json
import os
import shutil
from functools import partial
from optparse import make_option
from slugify import slugify

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import settings
from settings import LOG as logging, LOCAL_CONTENT_ROOT, LOCAL_CONTENT_DATA_PATH
from shared.topic_tools import get_topic_by_path, topics_file, get_topic_tree, get_all_leaves, get_path2node_map, get_parent
from utils.general import ensure_dir, get_kind_by_extension, humanize_name


class Command(BaseCommand):
    help = "Inegrate 3rd party content into KA Lite.\nUSAGE:\n  combine -l, -f to map and copy content into the system.\n use -d and -f to remove local content"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--directory-location', action='store', dest='location', default=None,
                    help='The full path of the base directory that contains the 3rd party content.'),
        make_option('-b', '--parent-path', action='store', dest='parent_path', default=None,
                    help='Parent node under which the given directory (topic) should be inserted under'),
        make_option('-f', '--file-name', action='store', dest='file_name', default=None,
                    help='The name of the file to write as a sibling to topics.json'),
        make_option('-d', '--delete-local-content', action='store_true', dest='flush_content', default=None,
                    help='For testing, delete the local_content directory first, before executing other commands.'),
        make_option('-R', '--restore', action='store_true', dest='restore', default=None,
                    help='For testing, restore topics.json to it\'s original state.'),
    )

    def handle(self, *args, **options):
        if options.get("restore"):
            restore()
        location = options.get("location")
        parent_path = options.get("parent_path")
        file_name = options.get("file_name")
        flush_content = options.get("flush_content")


        # Either we want to add content
        if location and parent_path and file_name and not flush_content:
            # Location must be valid
            if not os.path.exists(location):
                raise CommandError("The location given:'%s' does not exist on your computer. \
                    Please enter a valid directory." % location)
            # Base path must be valid
            # append trailing slash to parent_path if it's not there
            parent_path = parent_path if parent_path == "/" else parent_path + "/"
            if not get_topic_by_path(parent_path):
                raise CommandError("The base path:'%s' does not exist in topics.json. \
                    Please enter a valid base path." % parent_path)
            # File name must be unique
            if os.path.exists(os.path.join(settings.DATA_PATH, file_name)):
                raise CommandError("The file name '%s' is taken. \
                    Please specify a unique file name." % file_name)

            logging.info("Compiling data from %s for insertion to %s ..." % (location, parent_path))
            add_content(location, parent_path, file_name)
            logging.info("Successfully added content bundle %s" % file_name)

        # Or remove content
        elif flush_content and file_name and not (location and parent_path):
            # File name must exist
            if not os.path.exists(os.path.join(settings.DATA_PATH, file_name)):
                raise CommandError("The file name '%s' does not exist. \
                    Please specify a valid file name." % file_name)

            remove_content(file_name)
            logging.info("Successfully removed content bundle %s" % file_name)

        # Nothing else can happen
        else:
            raise CommandError("Must specify a combination of -l, -b, and -f \
                to add content OR -d and -f to remove content.")


def add_content(location, parent_path, file_name):
    """
    Take a "root" location and add content to system by mapping file
    hierarchy to JSON, copying content into the local_content directory,
    and updating the topic tree with the mapping inserted.
    """

    def construct_node(location, parent_path):
        """Return list of dictionaries of subdirectories and/or files in the location"""
        # Recursively add all subdirectories
        children = []

        dirpath = location
        base_name = os.path.basename(location)
        topic_slug = slugify(base_name)
        current_path = os.path.join(parent_path, topic_slug) + "/"
        node= {
            "kind": "Topic",
            "path": current_path,
            "id": topic_slug,
            "title": humanize_name(base_name),
            "slug": topic_slug,
            "description": "",
            "parent_id": os.path.basename(parent_path),
            "ancestor_ids": filter(None, parent_path.split("/")),  # TODO(bcipolli) get this from the parent node directly
            "hide": False,
            "children": [construct_node(os.path.join(location, s), current_path) for s in os.listdir(location) if os.path.isdir(os.path.join(location, s))],
        }

        # Add all files
        files = [f for f in os.listdir(location) if os.path.isfile(os.path.join(location, f))]
        for filepath in files:
            full_filename = os.path.basename(filepath)
            kind = get_kind_by_extension(full_filename)

            filename = os.path.splitext(full_filename)[0]
            extension = os.path.splitext(full_filename)[1].lower()
            file_slug = slugify(filename)
            node["children"].append({
                "youtube_id": file_slug,
                "id": file_slug,
                "title": humanize_name(filename),
                "path": os.path.join(current_path, file_slug) + "/",
                "ancestor_ids": filter(None, current_path.split("/")),
                "slug": file_slug,
                "parent_id": os.path.basename(topic_slug),
                "kind": kind,
            })

            # Copy over content
            ensure_dir(LOCAL_CONTENT_ROOT)
            normalized_filename = "%s%s" % (file_slug, extension)
            # shutil.copy(filepath, os.path.join(LOCAL_CONTENT_ROOT, normalized_filename))
            logging.info("Copied file %s to local content directory." % os.path.basename(filepath))

        # Finally, can add contains

        contains = set([])
        for ch in node["children"]:
            contains = contains.union(ch.get("contains", set([])))
            contains = contains.union(set([ch["kind"]]))
        node["contains"] = list(contains)

        return node

    def recurse_container(location):
        """Return list of kinds of containers beneath this location in the file hierarchy"""
        contains = set()
        if [f for f in os.listdir(location) if os.path.isfile(os.path.join(location, f))]:
            contains.add("Video") # TODO(dylan) assuming video here

        subdirectories = [os.path.join(location, s) for s in os.listdir(location) if os.path.isdir(os.path.join(location, s))]
        for dirpath in subdirectories:
            contains.add("Topic")
            contains.update(recurse_container(dirpath))
        return list(contains)

    # Generate topic_tree from file hierarchy
    nodes = construct_node(location, parent_path)

    # Write it to JSON
    ensure_dir(settings.LOCAL_CONTENT_DATA_PATH)
    write_location = os.path.join(settings.LOCAL_CONTENT_DATA_PATH, file_name)
    with open(write_location, "w") as dumpsite:
        json.dump(nodes, dumpsite, indent=4)
    logging.info("Wrote output to %s" % write_location)

    # Update topic tree with desired mapping
    inject_topic_tree(nodes, parent_path)


def inject_topic_tree(new_node, parent_path):
    """Insert all local content into topic_tree"""
    # Update portion of topic tree
    old_node = get_topic_by_path(new_node["path"])
    if old_node:
        logging.info("Updating node at path %s" % new_node["path"])
        old_node.update(new_node)
    else:
        logging.info("Inserting node to path %s" % new_node["path"])
        parent_node = get_topic_by_path(parent_path)
        parent_node["children"].append(new_node)

    # Write updated topic tree to disk
    topic_tree = get_topic_tree()
    topic_file_path = os.path.join(settings.DATA_PATH, topics_file)
    with open(topic_file_path, 'w') as f:
        json.dump(topic_tree, f, indent=4)
    logging.info("Rewrote topic tree: %s" % topic_file_path)

    # Regenerate node cache

# def remove_content(file_name):
#     """
#     Remove content from the system by deleting the mapping,
#     deleting any content contained in the mapping from the content
#     directory, and restoring the topic_tree to it's former glory.
#     """
#     if not os.path.exists(settings.LOCAL_CONTENT_DATA_PATH, file_name):
#         raise CommandError("Invalid name for local_content. File must exist inside ka-lite/data/local_content/")
#     with open(os.path.join(settings.LOCAL_CONTENT_DATA_PATH, file_name)) as f:
#         local_content = json.load(f)

#     def restore_topic_tree(local_content):
#         """Remove local_content from topics.json"""
#         topic_tree = get_topic_tree()
#         ## TODO topic_tree.deepsubtract(local_content)
#         with open(os.path.join(settings.DATA_PATH, topics_file), 'w') as f:
#             json.dump(topic_tree, f)

#     restore_topic_tree(local_content)

#     # Second, delete local content based on mapping
#     def delete_local_content(local_content):
#         """Remove local content videos from content directory"""
#         videos = get_all_leaves(local_content, "Video")
#         for v in videos:

    # Finally delete the mapping


def restore():
    os.remove(os.path.join(settings.DATA_PATH, "topics.json"))
    shutil.copy2(os.path.join(settings.DATA_PATH, "permtopics.json"), os.path.join(settings.DATA_PATH, "topics.json"))
