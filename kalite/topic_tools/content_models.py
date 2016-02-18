"""
This module acts as the only interface point between the main app and the database backend for the content.

It exposes several convenience functions for accessing content, which fall into two broad categories:

Topic functions - which return a limited set of fields, for use in rendering topic tree type structures.
Content functions - which return a full set of fields, for use in rendering content or reasoning about it.

In addition, content can either be returned in an exanded format, where all fields are directly represented on
the dictionary, or with many of the fields collapsed into an 'extra_fields' key.

All functions return the model data as a dictionary, in order to prevent external functions from having to know
implementation details about the model class used in this module.
"""
import os
import json

import sqlite3
import itertools

from peewee import Model, SqliteDatabase, CharField, TextField, BooleanField, ForeignKeyField, PrimaryKeyField, Using,\
    DoesNotExist, fn, IntegerField, OperationalError, FloatField

from playhouse.shortcuts import model_to_dict

from .base import available_content_databases
from .settings import CONTENT_DATABASE_PATH, CHANNEL
from .annotate import update_content_availability

from django.conf import settings; logging = settings.LOG


# This Item is defined without a database.
# This allows us to use a separate database for each language, so that we
# can reduce performance cost, and keep queries simple for multiple languages.
# In addition, we can distribute databases separately for each language pack.
class Item(Model):
    title = CharField()
    description = TextField()
    available = BooleanField()
    files_complete = IntegerField(default=0)
    total_files = IntegerField(default=0)
    kind = CharField()
    parent = ForeignKeyField("self", null=True, index=True, related_name="children")
    id = CharField(index=True)
    pk = PrimaryKeyField(primary_key=True)
    slug = CharField()
    path = CharField(index=True, unique=True)
    extra_fields = CharField(null=True)
    youtube_id = CharField(null=True)
    size_on_disk = IntegerField(default=0)
    remote_size = IntegerField(default=0)
    sort_order = FloatField(default=0)

    class Meta:
        # Order by sort_order by default for all queries.
        order_by = ('sort_order',)

    def __init__(self, *args, **kwargs):
        kwargs = parse_model_data(kwargs)
        super(Item, self).__init__(*args, **kwargs)

class AssessmentItem(Model):
    id = CharField(max_length=50)
    # looks like peewee doesn't like a primary key field that's not an integer.
    # Hence, we have a separate field for the primary key.
    pk = PrimaryKeyField(primary_key=True)
    item_data = TextField()  # A serialized JSON blob
    author_names = CharField(max_length=200)  # A serialized JSON list


def parse_model_data(item):
    extra_fields = item.get("extra_fields", {})

    if type(extra_fields) is not dict:
        extra_fields = json.loads(extra_fields)

    remove_keys = []
    for key, value in item.iteritems():
        if key not in Item._meta.fields:
            extra_fields[key] = value
            remove_keys.append(key)

    for key in remove_keys:
        del item[key]

    item["extra_fields"] = json.dumps(extra_fields)
    return item


def unparse_model_data(item):

    extra_fields = json.loads(item.get("extra_fields", "{}"))

    # Do this to ensure any model fields that have accidentally
    # been folded into extra fields are not overwritten on output
    extra_fields.update(item)
    return extra_fields


def set_database(function):
    """
    Sets the appropriate database for the ensuing model interactions.
    """

    def wrapper(*args, **kwargs):
        # Hardcode the Brazilian Portuguese mapping that only the central server knows about
        # TODO(jamalex): BURN IT ALL DOWN!
        language = kwargs.get("language", "en")

        if language == "pt-BR":
            language = "pt"

        path = kwargs.pop("database_path", None) or CONTENT_DATABASE_PATH.format(channel=kwargs.get("channel", CHANNEL), language=language)

        db = SqliteDatabase(path)

        kwargs["db"] = db

        db.connect()

        # This should contain all models in the database to make them available to the wrapped function

        with Using(db, [Item, AssessmentItem]):

            try:

                output = function(*args, **kwargs)

            except DoesNotExist:
                output = None

            except OperationalError:
                logging.error("No content database file found")
                raise
        db.close()

        return output
    return wrapper


def parse_data(function):
    """
    Parses the output of functions to be dicts (and expanded extra_fields if needed)
    """

    def wrapper(*args, **kwargs):

        dicts = kwargs.get("dicts", True)

        expanded = kwargs.get("expanded", True)

        output = function(*args, **kwargs)

        if dicts and output:
            try:
                if expanded:
                    output = map(unparse_model_data, output.dicts())
                else:
                    output = [item for item in output.dicts()]
            except (TypeError, OperationalError) as e:
                logging.warn("No content database file found")
                output = []
        return output
    return wrapper


@parse_data
@set_database
def get_random_content(kinds=None, limit=1, **kwargs):
    """
    Convenience function for returning random content nodes for use in testing
    :param kinds: A list of node kinds to select from.
    :param limit: The maximum number of items to return.
    :return: A list of randomly selected content dictionaries.
    """
    if not kinds:
        kinds = ["Video", "Audio", "Exercise", "Document"]
    return Item.select().where(Item.kind.in_(kinds)).order_by(fn.Random()).limit(limit)


@set_database
def get_content_item(content_id=None, topic=False, **kwargs):
    """
    Convenience function for returning a fully fleshed out content node for use in rendering content
    To save server processing, the extra_fields are fleshed out on the client side.
    By default, don't return topic nodes to avoid id collisions.
    :param content_id: The content_id to select by - caution, this is a non-unique field.
    :param topic: Return non-topic or topic nodes - default to non-topics.
    :return: A single content dictionary.
    """
    if content_id:
        # Ignore topics in case of id collision.
        if topic:
            value = Item.get(Item.id == content_id, Item.kind == "Topic")
        else:
            value = Item.get(Item.id == content_id, Item.kind != "Topic")
        return model_to_dict(value)


@parse_data
@set_database
def get_content_items(ids=None, **kwargs):
    """
    Convenience function for returning multiple topic tree nodes for use in rendering content
    :param ids: A list of node ids to select - as ids are non-unique a single id may return multiple content items.
    :return: A list of content dictionaries.
    """
    if ids:
        values = Item.select().where(Item.id.in_(ids))
    else:
        values = Item.select()
    return values


@parse_data
@set_database
def get_topic_nodes(parent=None, ids=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the topic tree
    Can either pass in the parent id to return all the immediate children of a node,
    or a list of ids to return an arbitrary set of nodes with limited fields.
    :param parent: id of a parent node (always a topic).
    :param ids: A list of ids to return.
    :return: A list of content dictionaries with limited fields.
    """
    if parent:
        Parent = Item.alias()
        if parent == "root":
            selector = Parent.parent.is_null()
        else:
            selector = Parent.id == parent
        values = Item.select(
            Item.title,
            Item.description,
            Item.available,
            Item.kind,
            Item.children,
            Item.id,
            Item.path,
            Item.slug,
        ).join(Parent, on=(Item.parent == Parent.pk)).where(selector & Item.available)
        return values
    elif ids:
        values = Item.select(
            Item.title,
            Item.description,
            Item.available,
            Item.kind,
            Item.children,
            Item.id,
            Item.path,
            Item.slug,
        ).where(Item.id.in_(ids))
        return values


@parse_data
@set_database
def get_topic_update_nodes(parent=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the update topic tree
    :param parent: id of a parent node (always a topic).
    :return: A list of content dictionaries with limited fields.
    """
    if parent:
        Parent = Item.alias()
        if parent == "root":
            selector = Parent.parent.is_null()
        else:
            selector = Parent.id == parent
        values = Item.select(
            Item.title,
            Item.description,
            Item.available,
            Item.kind,
            Item.pk,
            Item.size_on_disk,
            Item.remote_size,
            Item.files_complete,
            Item.total_files,
            Item.id,
            Item.path,
        ).join(Parent, on=(Item.parent == Parent.pk)).where((selector) & (Item.total_files != 0))
        return values


@set_database
def get_topic_node(content_id=None, topic=True, **kwargs):
    """
    Convenience function for returning a topic/content node with limited fields
    :param content_id: A list of ids to return.
    :return: A list of content dictionaries with limited fields.
    """
    if content_id:
        if topic:
            kind_selector = Item.kind == "Topic"
        else:
            kind_selector = Item.kind != "Topic"
        value = Item.select(
            Item.title,
            Item.description,
            Item.available,
            Item.kind,
            Item.children,
            Item.id,
            Item.path,
            Item.slug,
        ).where((Item.id == content_id) & (kind_selector)).get()
        return model_to_dict(value)


@set_database
def get_topic_nodes_with_children(parent=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with children listed as ids.
    Used for parsing and traversing the topic tree in content recommendation.
    :param parent: id of a parent node (always a topic).
    :return: A list of content dictionaries with the specified parent, with a children field as a list of ids.
    """
    if parent:
        Parent = Item.alias()
        Child = Item.alias()
        if parent == "root":
            selector = Parent.parent.is_null()
        else:
            selector = Parent.id == parent
        child_values = [item for item in Item.select(
            Child
        ).join(Child, on=(Child.parent == Item.pk)).join(Parent, on=(Item.parent == Parent.pk)).where(selector).dicts()]
        parent_values = [item for item in Item.select(
            Item
        ).join(Parent, on=(Item.parent == Parent.pk)).where(selector).dicts()]
        topics = []
        for topic in parent_values:
            output = {}
            output.update(topic)
            output["children"] = [child["id"] for child in child_values if child["parent"] == topic["pk"]]
            topics.append(output)
        return topics


@parse_data
@set_database
def get_content_parents(ids=None, **kwargs):
    """
    Convenience function for returning all parent nodes of a set of content as specified by ids.
    :param ids: A list of topic ids.
    :return: A list of content dictionaries.
    """
    if ids:
        Parent = Item.alias()
        parent_values = Item.select(
            Parent
        ).join(Parent, on=(Item.parent == Parent.pk)).where(Item.id.in_(ids)).distinct()
        if parent_values is None:
            parent_values = list()
        return parent_values
    else:
        return list()



@parse_data
@set_database
def get_leafed_topics(kinds=None, db=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes that contain content
    """
    if not kinds:
        kinds = ["Video", "Audio", "Exercise", "Document"]

    Parent = Item.alias()
    parent_values = Item.select(
        Parent
    ).join(Parent, on=(Item.parent == Parent.pk)).where(Item.kind.in_(kinds)).distinct()
    return parent_values


@parse_data
@set_database
def get_topic_contents(kinds=None, topic_id=None, **kwargs):
    """
    Convenience function for returning a set of content/leaf nodes contained within a topic
    :param kinds: A list of content kinds to select from.
    :param topic_id: The id of the topic to select within.
    :return: A list of content dictionaries.
    """
    if topic_id:
        topic_node = Item.get(Item.id == topic_id, Item.kind == "Topic")

        if not kinds:
            kinds = ["Video", "Audio", "Exercise", "Document"]
        return Item.select(Item).where(Item.kind.in_(kinds), Item.path.contains(topic_node.path))


@set_database
def get_download_youtube_ids(paths=None, **kwargs):
    """
    Convenience function for taking a list of content ids and returning
    all associated youtube_ids for downloads, regardless of whether the input
    paths are paths for content nodes or topic nodes
    :param paths: A list of paths to nodes - used to ensure uniqueness.
    :return: A unique list of youtube_ids as strings.
    """
    if paths:
        youtube_ids = dict()
        for path in paths:
            selector = (Item.kind != "Topic") & (Item.path.contains(path)) & (Item.youtube_id.is_null(False))

            youtube_ids.update(dict([item for item in Item.select(Item.youtube_id, Item.title).where(selector).tuples() if item[0]]))

        return youtube_ids


def get_video_from_youtube_id(youtube_id):
    """
    This function is provided to ensure that the data migration 0029_set_video_id_for_realz
    in the main app is still able to be run if needed.
    It searches through every available content database in order to find the associated content id
    for a particular youtube id.
    :param youtube_id: String containing a youtube id.
    :return: A dictionary containing video metadata.
    """
    for channel, language in available_content_databases():
        video = _get_video_from_youtube_id(channel=channel, language=language, youtube_id=youtube_id)
        if video:
            return video


@parse_data
@set_database
def _get_video_from_youtube_id(youtube_id=None, **kwargs):
    """
    Convenience function for returning a fully fleshed out video content node from youtube_id
    :param youtube_id: String containing a youtube id.
    :return: A dictionary containing video metadata.
    """
    if youtube_id:
        value = Item.get(Item.youtube_id == youtube_id, Item.kind == "Video")
        return model_to_dict(value)


@set_database
def search_topic_nodes(kinds=None, query=None, page=1, items_per_page=10, exact=True, **kwargs):
    """
    Search all nodes and return limited fields.
    :param kinds: A list of content kinds.
    :param query: Text string to search for in titles or extra fields.
    :param page: Which page of the paginated search to return.
    :param items_per_page: How many items on each page of the paginated search.
    :param exact: Flag to allow for an exact match, if false, always return more than one item.
    :return: A list of dictionaries containing content metadata.
    """
    if query:
        if not kinds:
            kinds = ["Video", "Audio", "Exercise", "Document", "Topic"]
        try:
            topic_node = Item.select(
                Item.title,
                Item.description,
                Item.available,
                Item.kind,
                Item.id,
                Item.path,
                Item.slug,
            ).where((fn.Lower(Item.title) == query) & (Item.kind.in_(kinds))).get()
            if exact:
                # If allowing an exact match, just return that one match and we're done!
                return [model_to_dict(topic_node)], True, None
        except DoesNotExist:
            topic_node = {}
            pass
        # For efficiency, don't do substring matches when we've got lots of results
        topic_nodes = Item.select(
            Item.title,
            Item.description,
            Item.available,
            Item.kind,
            Item.id,
            Item.path,
            Item.slug,
        ).where((Item.kind.in_(kinds)) & ((fn.Lower(Item.title).contains(query)) | (fn.Lower(Item.extra_fields).contains(query))))
        pages = topic_nodes.count()/items_per_page
        topic_nodes = [item for item in topic_nodes.paginate(page, items_per_page).dicts()]
        if topic_node:
            # If we got an exact match, show it first.
            topic_nodes.insert(0, model_to_dict(topic_node))
        return topic_nodes, False, pages


@set_database
def bulk_insert(items, **kwargs):
    """
    Insert many rows into the database at once.
    Limit to 500 items at a time for performance reasons.
    :param items: List of dictionaries containing content metadata.
    """
    if items:
        db = kwargs.get("db")
        items = map(parse_model_data, items)
        if db:
            with db.atomic():
                for idx in range(0, len(items), 500):
                    Item.insert_many(map(parse_model_data, items[idx:idx+500])).execute()


@set_database
def get_or_create(item, **kwargs):
    """
    Wrapper around get or create that allows us to specify a database
    and also parse the model data to compress extra fields.
    :param item: A dictionary containing content metadata for one node.
    """
    if item:
        Item.create_or_get(**parse_model_data(item))


@set_database
def update_item(update=None, path=None, **kwargs):
    """
    Select an item by path, update fields and save.
    Updates all items that have the same id as well.
    Ids are not unique due to denormalization, yet items with the same id should have the same info.

    :param update: Dictionary of attributes to update on the model.
    :param path: Unique path for the content node to be updated. Also updates nodes with the same id.
    """
    if update and path:
        base_item = Item.get(Item.path == path)
        items = Item.select().where((Item.id == base_item.id) & (Item.kind == base_item.kind))
        for item in items:
            if any(key not in Item._meta.fields for key in update):
                item_data = unparse_model_data(item)
                item_data.update(update)
                for key, value in parse_model_data(item_data).iteritems():
                    setattr(item, key, value)
            else:
                for key, value in update.iteritems():
                    setattr(item, key, value)

            item.save()


def iterator_content_items(ids=None, **kwargs):
    """
    Generator to iterate over content items specified by ids,
    run update content availability on that item and then yield the
    required update.
    :param update: Dictionary of attributes to update on the model.
    :yield: Tuple of unique path to item, and the update to be carried out on that item
    """
    if ids:
        items = Item.select().where(Item.id.in_(ids)).dicts().iterator()
    else:
        items = Item.select().dicts().iterator()

    mapped_items = itertools.imap(unparse_model_data, items)
    updated_mapped_items = update_content_availability(mapped_items)

    for path, update in updated_mapped_items:
        yield path, update


def iterator_content_items_by_youtube_id(ids=None, **kwargs):
    """
    Generator to iterate over content items specified by youtube ids,
    run update content availability on that item and then yield the
    required update.
    :param update: Dictionary of attributes to update on the model.
    :yield: Tuple of unique path to item, and the update to be carried out on that item
    """
    if ids:
        items = Item.select().where(Item.youtube_id.in_(ids)).dicts().iterator()
    else:
        items = Item.select().dicts().iterator()

    mapped_items = itertools.imap(unparse_model_data, items)
    updated_mapped_items = update_content_availability(mapped_items)

    for path, update in updated_mapped_items:
        yield path, update


@set_database
def create_table(**kwargs):
    """
    Create a table in the database.
    """
    db = kwargs.get("db")
    if db:
        db.create_tables([Item, AssessmentItem])


def annotate_content_models_by_youtube_id(channel="khan", language="en", youtube_ids=None):
    """
    Annotate content models that have the youtube ids specified in a list.
    :param channel: Channel to update.
    :param language: Language of channel to update.
    :param youtube_ids: List of youtube_ids to find content models for annotation.
    """
    annotate_content_models(channel=channel, language=language, ids=youtube_ids, iterator_content_items=iterator_content_items_by_youtube_id)


@set_database
def annotate_content_models(channel="khan", language="en", ids=None, iterator_content_items=iterator_content_items, **kwargs):
    """
    Annotate content models that have the ids specified in a list.
    Our ids can be duplicated at the moment, so this may be several content items per id.
    When a content item has been updated, propagate availability up the topic tree.
    :param channel: Channel to update.
    :param language: Language of channel to update.
    :param ids: List of content ids to find content models for annotation.
    :param iterator_content_items: Generator function to use to yield paths and updates.
    """

    db = kwargs.get("db")
    if db:
        content_models = iterator_content_items(ids=ids)
        with db.atomic() as transaction:
            def recurse_availability_up_tree(node, available):
                if not node.parent:
                    return
                else:
                    parent = node.parent
                Parent = Item.alias()
                children = Item.select().join(Parent, on=(Item.parent == Parent.pk)).where(Item.parent == parent.pk)
                if not available:
                    children_available = children.where(Item.available == True).count() > 0
                    available = children_available

                files_complete = children.aggregate(fn.SUM(Item.files_complete))

                child_remote = children.where(((Item.available == False) & (Item.kind != "Topic")) | (Item.kind == "Topic")).aggregate(fn.SUM(Item.remote_size))
                child_on_disk = children.aggregate(fn.SUM(Item.size_on_disk))

                if parent.available != available:
                    parent.available = available
                if parent.files_complete != files_complete:
                    parent.files_complete = files_complete
                # Ensure that the aggregate sizes are not None
                if parent.remote_size != child_remote and child_remote:
                    parent.remote_size = child_remote
                # Ensure that the aggregate sizes are not None
                if parent.size_on_disk != child_on_disk and child_on_disk:
                    parent.size_on_disk = child_on_disk
                if parent.is_dirty():
                    parent.save()
                    recurse_availability_up_tree(parent, available)

            for path, update in content_models:
                if update:
                    # We have duplicates in the topic tree, make sure the stamping happens to all of them.
                    item = Item.get(Item.path == path)
                    if item.kind != "Topic":
                        item_data = unparse_model_data(model_to_dict(item, recurse=False))
                        item_data.update(update)
                        item_data = parse_model_data(item_data)
                        for attr, val in item_data.iteritems():
                            setattr(item, attr, val)
                        item.save()
                        recurse_availability_up_tree(item, update.get("available", False))


@set_database
def update_parents(parent_mapping=None, **kwargs):
    """
    Convenience function to add parent nodes to other nodes in the database.
    Needs a mapping from item path to parent id.
    As only Topics can be parents, and we can have duplicate ids, we filter on both.
    :param update_mapping: A dictionary containing item paths as keys, with parent ids as values.
    """

    if parent_mapping:
        db = kwargs.get("db")
        if db:
            with db.atomic() as transaction:
                for key, value in parent_mapping.iteritems():
                    if value:
                        try:
                            # Only Topics can be parent nodes
                            parent = Item.get(Item.id == value, Item.kind == "Topic")
                            item = Item.get(Item.path == key)
                        except DoesNotExist:
                            print(key, value, "Parent or Item not found")
                        if item and parent:
                            item.parent = parent
                            item.save()


@set_database
def get_assessment_item_data(assessment_item_id=None, **kwargs):
    """
    Wrapper function to return assessment_item from database as a dictionary.
    :param assessment_item_id: id of the assessment item to return.
    :return: Dictionary containing assessment item data.
    """
    try:
        assessment_item = AssessmentItem.get(AssessmentItem.id == assessment_item_id)
        return model_to_dict(assessment_item)
    except OperationalError:
        return {}
