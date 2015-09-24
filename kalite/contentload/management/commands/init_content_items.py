"""
Management command to take JSON files with metadata for the topic tree, exercise and content caches
and turn them into a single database file
"""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from fle_utils.general import softload_json
from optparse import make_option

from django.conf import settings as django_settings
logging = django_settings.LOG

from kalite.topic_tools.content_models import bulk_insert, get_or_create, create_table, update_parents

from kalite.contentload import settings
from kalite.contentload.utils import dedupe_paths

from kalite.topic_tools.settings import CONTENT_DATABASE_PATH, CHANNEL_DATA_PATH

from kalite import i18n
from django.utils.translation import gettext as _


def generate_topic_tree_items(channel="khan", language="en"):
    """
    Read in all relevant JSON data, recurse over all nodes, and add in the data from the content caches
    to fully flesh out those nodes in the topic tree.

    Returns a list of topic tree nodes (topic, content, and exercise) and a mapping of children to parents.
    Need to make this list now, as the pk for each item is not available at row creation in the database,
    so it has to be added after the fact.
    """

    flat_topic_tree = []

    parental_units = {}

    channel_data_path = os.path.join(django_settings.CONTENT_DATA_PATH, channel)

    topic_tree = softload_json(os.path.join(channel_data_path, "topics.json"), logger=logging.debug, raises=False)
    content_cache = softload_json(os.path.join(channel_data_path, "contents.json"), logger=logging.debug, raises=False)
    exercise_cache = softload_json(os.path.join(channel_data_path, "exercises.json"), logger=logging.debug, raises=False)

    def recurse_nodes(node, parent=""):
        """
        Recurse the nodes of the topic tree to trace parent child relations
        and substitute full content nodes for denormed nodes.
        """

        parental_units[node.get("path")] = parent

        node.pop("child_data", None)

        child_availability = []

        child_ids = [child.get("id") for child in node.get("children", [])]

        # Do the recursion
        for child in node.get("children", []):
            recurse_nodes(child, node.get("id"))
            child_availability.append(child.get("available", False))

        node.pop("children", None)

        if node.get("kind") != "Topic":

            if node.get("kind") == "Exercise":
                data = exercise_cache.get(node.get("id"), {})
            else:
                data = content_cache.get(node.get("id"), {})

            node = dict(data, **node)
        node["available"] = False

        # Translate everything for good measure
        with i18n.translate_block(language):
            node["title"] = _(node.get("title", ""))
            node["description"] = _(node.get("description", "")) if node.get("description") else ""

        flat_topic_tree.append(node)

    dedupe_paths(topic_tree)

    recurse_nodes(topic_tree)

    return flat_topic_tree, parental_units



class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-f", "--content-items-folderpath",
                    action="store",
                    dest="content_items_filepath",
                    default=CHANNEL_DATA_PATH,
                    help="Override the JSON data source to import assessment items from"),
        make_option("-d", "--database-path",
                    action="store",
                    dest="database_path",
                    default="",
                    help="Override the destination path for the content item DB file"),
        make_option("-b", "--no-bulk-create",
                    action="store_true",
                    dest="no_bulk_create",
                    default=False,
                    help="Create the records in bulk (warning: will delete destination DB first)"),
        make_option("-c", "--channel",
                    action="store",
                    dest="channel",
                    default="khan",
                    help="Channel to generate database for."),
        make_option("-l", "--language",
                    action="store",
                    dest="language",
                    default="en",
                    help="Language to create database for."),
        make_option("-o", "--overwrite",
                    action="store_true",
                    dest="overwrite",
                    default=False,
                    help="Overwrite existing Database"),
    )

    def handle(self, *args, **kwargs):

        language = kwargs["language"]
        channel = kwargs["channel"]
        # temporarily swap out the database path for the desired target
        database_path = kwargs["database_path"] or CONTENT_DATABASE_PATH.format(channel=channel, language=language)
        bulk_create = not kwargs["no_bulk_create"]

        if bulk_create and os.path.isfile(database_path):
            if kwargs["overwrite"]:
                os.remove(database_path)
            else:
                logging.info("Database already exists, use --overwrite to force overwrite")
                return None

        if not os.path.isfile(database_path):
            logging.info("Creating database file at {path}".format(path=database_path))
            create_table(database_path=database_path)

        channel_data_path = kwargs.get("content_items_filepath")

        logging.info("Generating flattened topic tree for import")

        items, parental_units = generate_topic_tree_items(channel=channel, language=language)

        if bulk_create:
            logging.info("Bulk creating {number} topic and content items".format(number=len(items)))
            bulk_insert(items, database_path=database_path)
        else:
            logging.info("Individually creating {number} topic and content items".format(number=len(items)))
            for item in items:
                get_or_create(item, database_path=database_path)

        logging.info("Adding parent mapping information to nodes")
        update_parents(parent_mapping=parental_units, database_path=database_path)
        logging.info("Database creation completed successfully")
