"""
Management command to take JSON files with metadata for the topic tree, exercise and content caches
and turn them into a single database file
"""

import os

from django.core.management.base import BaseCommand
from fle_utils.general import softload_json
from optparse import make_option

from django.conf import settings as django_settings
logging = django_settings.LOG

from kalite.topic_tools.content_models import bulk_insert, create_table, update_parents

from kalite.contentload.utils import dedupe_paths

from kalite.topic_tools.settings import CONTENT_DATABASE_TEMPLATE_PATH, CHANNEL_DATA_PATH

from kalite.i18n.base import translate_block

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

    channel_data_path = CHANNEL_DATA_PATH

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

        total_files = 0

        # Do the recursion
        for child in node.get("children", []):
            total_files += recurse_nodes(child, node.get("id"))

        node.pop("children", None)

        if node.get("kind") != "Topic":

            if node.get("kind") == "Exercise":
                data = exercise_cache.get(node.get("id"), {})
            else:
                data = content_cache.get(node.get("id"), {})
                total_files = 1

            node = dict(data, **node)

        node["total_files"] = total_files

        node["available"] = False

        # Translate everything for good measure
        with translate_block(language):
            node["title"] = _(node.get("title", ""))
            node["description"] = _(node.get("description", "")) if node.get("description") else ""

        flat_topic_tree.append(node)
        return total_files

    dedupe_paths(topic_tree)

    recurse_nodes(topic_tree)

    return flat_topic_tree, parental_units


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
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
        database_path = CONTENT_DATABASE_TEMPLATE_PATH.format(channel=channel, language=language)

        if not os.path.exists(django_settings.DB_CONTENT_ITEM_TEMPLATE_DIR):
            os.makedirs(django_settings.DB_CONTENT_ITEM_TEMPLATE_DIR)

        if os.path.isfile(database_path):
            if kwargs["overwrite"]:
                os.remove(database_path)
            else:
                logging.info("Database already exists, use --overwrite to force overwrite")
                return None

        if not os.path.isfile(database_path):
            logging.info("Creating database file at {path}".format(path=database_path))
            create_table(database_path=database_path)

        logging.info("Generating flattened topic tree for import")

        items, parental_units = generate_topic_tree_items(channel=channel, language=language)

        logging.info("Bulk creating {number} topic and content items".format(number=len(items)))
        bulk_insert(items, database_path=database_path)

        logging.info("Adding parent mapping information to nodes")
        update_parents(parent_mapping=parental_units, database_path=database_path)
        logging.info("Database creation completed successfully")
