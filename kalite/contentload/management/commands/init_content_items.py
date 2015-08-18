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

from kalite.topic_tools.settings import CONTENT_DATABASE_PATH

from kalite import i18n
from django.utils.translation import gettext as _


def generate_topic_tree_items(channel="khan", language="en"):
    flat_topic_tree = []

    parental_units = {}

    channel_data_path = os.path.join(django_settings.CONTENT_DATA_PATH, channel)

    topic_tree = softload_json(os.path.join(channel_data_path, "topics.json"), logger=logging.debug, raises=False)
    content_cache = softload_json(os.path.join(channel_data_path, "contents.json"), logger=logging.debug, raises=False)
    exercise_cache = softload_json(os.path.join(channel_data_path, "exercises.json"), logger=logging.debug, raises=False)

    def recurse_nodes(node, parent=""):

        parental_units[node.get("id")] = parent

        node.pop("child_data", None)

        child_availability = []

        child_ids = [child.get("id") for child in node.get("children", [])]

        # Do the recursion
        for child in node.get("children", []):
            recurse_nodes(child, node.get("id"))
            child_availability.append(child.get("available", False))

        node.pop("children", None)

        # If child_availability is empty then node has no children so we can determine availability
        if child_availability:
            node["available"] = any(child_availability)
        else:
            # By default this is very charitable, assuming if something has not been annotated
            # it is available.
            if node.get("kind") == "Exercise":
                node.update(exercise_cache.get(node.get("id"), {}))
            else:
                node.update(content_cache.get(node.get("id"), {}))
            node["available"] = False

        # Translate everything for good measure
        with i18n.translate_block(language):
            node["title"] = _(node.get("title", ""))
            node["description"] = _(node.get("description", "")) if node.get("description") else ""

        flat_topic_tree.append(node)

    recurse_nodes(topic_tree)

    return flat_topic_tree, parental_units



class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-f", "--content-items-folderpath",
                    action="store",
                    dest="content_items_filepath",
                    default=django_settings.CHANNEL_DATA_PATH,
                    help="Override the JSON data source to import assessment items from"),
        make_option("-d", "--database-path",
                    action="store",
                    dest="database_path",
                    default="",
                    help="Override the destination path for the assessment item DB file"),
        make_option("-b", "--bulk-create",
                    action="store_true",
                    dest="bulk_create",
                    default=True,
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
    )

    def handle(self, *args, **kwargs):

        language = kwargs["language"]
        channel = kwargs["channel"]
        # temporarily swap out the database path for the desired target
        database_path = kwargs["database_path"] or CONTENT_DATABASE_PATH.format(channel=channel, language=language)
        bulk_create = kwargs["bulk_create"]

        if bulk_create and os.path.isfile(database_path):
            os.remove(database_path)

        channel_data_path = kwargs.get("content_items_filepath")

        items, parental_units = generate_topic_tree_items(channel=channel, language=language)

        delete_ids = []

        node_ids = []

        for i, item in enumerate(items):
            if item.get("id") in node_ids:
                delete_ids.append(i)
            else:
                node_ids.append(item.get("id"))

        for i in reversed(delete_ids):
            items.pop(i)

        create_table(database_path=database_path)

        if bulk_create:
            bulk_insert(items, database_path=database_path)
        else:
            for k, v in raw_items.iteritems():
                get_or_create(items, database_path=database_path)

        update_parents(parent_mapping=parental_units, database_path=database_path)