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

from peewee import Model, SqliteDatabase, CharField, TextField, BooleanField, ForeignKeyField, PrimaryKeyField, Using, DoesNotExist, fn
from playhouse.shortcuts import model_to_dict

from .settings import CONTENT_DATABASE_PATH, CHANNEL
from .annotate import update_content_availability


# This BaseItem is used to subclass different Models for different languages.
# This allows us to use a separate database for each language, so that we
# can reduce performance cost, and keep queries simple for multiple languages.
# In addition, we can distribute databases separately for each language pack.
class Item(Model):
    title = CharField()
    description = TextField()
    available = BooleanField()
    kind = CharField()
    parent = ForeignKeyField("self", null=True, index=True, related_name="children")
    id = CharField(index=True)
    pk = PrimaryKeyField(primary_key=True)
    slug = CharField()
    path = CharField(index=True, unique=True)
    extra_fields = CharField(null=True)

    def __init__(self, *args, **kwargs):
        kwargs = parse_model_data(kwargs)
        super(Item, self).__init__(*args, **kwargs)


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

    item.update(extra_fields)
    return item


def database_exists(channel="khan", language="en", database_path=None):
    path = database_path or CONTENT_DATABASE_PATH.format(channel=channel, language=language)

    return os.path.exists(path)


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

        try:

            output = function(*args, **kwargs)

        except DoesNotExist:
            output = None

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
            if expanded:
                output = map(unparse_model_data, output.dicts())
            else:
                output = [item for item in output.dicts()]

        return output
    return wrapper


@parse_data
@set_database
def get_random_content(kinds=None, limit=1, db=None):
    """
    Convenience function for returning random content nodes for use in testing
    """
    with Using(db, [Item]):
        if not kinds:
            kinds = ["Video", "Audio", "Exercise", "Document"]
        return Item.select().where(Item.kind.in_(kinds)).order_by(fn.Random()).limit(limit)


@set_database
def get_content_item(content_id=None, db=None, topic=False, **kwargs):
    """
    Convenience function for returning a fully fleshed out content node for use in rendering content
    To save server processing, the extra_fields are fleshed out on the client side.
    By default, don't return topic nodes to avoid id collisions.
    """
    if content_id:
        with Using(db, [Item]):
            # Ignore topics in case of id collision.
            if topic:
                value = Item.get(Item.id == content_id, Item.kind == "Topic")
            else:
                value = Item.get(Item.id == content_id, Item.kind != "Topic")
            return model_to_dict(value)


@parse_data
@set_database
def get_content_items(ids=None, db=None, **kwargs):
    """
    Convenience function for returning multiple topic tree nodes for use in rendering content
    """
    with Using(db, [Item]):
        if ids:
            values = Item.select().where(Item.id.in_(ids))
        else:
            values = Item.select()
        return values


@parse_data
@set_database
def get_topic_nodes(parent=None, ids=None, db=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the topic tree
    Can either pass in the parent id to return all the immediate children of a node,
    or a list of ids to return an arbitrary set of nodes with limited fields.
    """
    if parent:
        with Using(db, [Item]):
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
                ).join(Parent, on=(Item.parent == Parent.pk)).where(selector)
            return values
    elif ids:
        with Using(db, [Item]):
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


@set_database
def get_topic_node(content_id=None, db=None, **kwargs):
    """
    Convenience function for returning a topic/content node with limited fields
    """
    if content_id:
        with Using(db, [Item]):
            value = Item.select(
                Item.title,
                Item.description,
                Item.available,
                Item.kind,
                Item.children,
                Item.id,
                Item.path,
                Item.slug,
                ).where(Item.id == content_id)
            return model_to_dict(value)


@set_database
def get_topic_nodes_with_children(parent=None, db=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the topic tree
    """
    if parent:
        with Using(db, [Item]):
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
def get_content_parents(ids=None, db=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the topic tree
    """
    if ids:
        with Using(db, [Item]):
            Parent = Item.alias()
            parent_values = Item.select(
                Parent
                ).join(Parent, on=(Item.parent == Parent.pk)).where(Item.id.in_(ids))
            return parent_values


@parse_data
@set_database
def get_topic_contents(kinds=None, topic_id=None, db=None, **kwargs):
    """
    Convenience function for returning a set of nodes for a topic
    """
    if topic_id:
        with Using(db, [Item]):
            topic_node = Item.get(Item.id == topic_id)

            if not kinds:
                kinds = ["Video", "Audio", "Exercise", "Document", "Topic"]
            return Item.select(Item).where(Item.kind.in_(kinds), Item.path.contains(topic_node.path))


@set_database
def search_topic_nodes(kinds=None, query=None, db=None, page=1, items_per_page=10, exact=True, **kwargs):
    """
    Search all nodes and return limited fields.
    """
    if query:
        with Using(db, [Item]):
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
                topic_nodes = [model_to_dict(topic_node)] + topic_nodes
            return topic_nodes, False, pages


@set_database
def bulk_insert(items, db=None, **kwargs):
    """
    Insert many rows into the database at once.
    Limit to 500 items at a time for performance reasons.
    """
    if items:
        items = map(parse_model_data, items)
        with Using(db, [Item]):
            with db.atomic():
                for idx in range(0, len(items), 500):
                    Item.insert_many(map(parse_model_data, items[idx:idx+500])).execute()


@set_database
def get_or_create(item, db=None, **kwargs):
    """
    Wrapper around get or create that allows us to specify a database
    and also parse the model data to compress extra fields.
    """
    if item:
        with Using(db, [Item]):
            Item.create_or_get(**parse_model_data(item))


@set_database
def update(update=None, select=None, **kwargs):
    """
    Think wrapper around update to select database.
    """
    if update:
        with Using(db, [Item]):
            if select:
                query = Item.update(**update).select(select)
            else:
                query = Item.update(**update)

            query.execute()


@set_database
def create_table(db=None, **kwargs):
    """
    Create a table in the database.
    """
    with Using(db, [Item]):
        db.create_tables([Item])


@set_database
def annotate_content_models(db=None, channel="khan", language="en", ids=None, **kwargs):
    """
    Annotate content models that have the ids specified in a list.
    Our ids can be duplicated at the moment, so this may be several content items per id.
    When a content item has been updated, propagate availability up the topic tree.
    """
    content_models = get_content_items(ids=ids, channel=channel, language=language)
    updates_dict = update_content_availability(content_models)

    with Using(db, [Item]):

        with db.atomic() as transaction:
            def recurse_availability_up_tree(node, available):
                if not node.parent:
                    return
                else:
                    parent = node.parent
                if not available:
                    Parent = Item.alias()
                    children_available = Item.select().join(Parent, on=(Item.parent == Parent.pk)).where(Item.parent == parent.pk, Item.available == True).count() > 0
                    available = children_available
                if parent.available != available:
                    parent.available = available
                    parent.save()
                    recurse_availability_up_tree(parent, available)


            for path, update in updates_dict.iteritems():
                if update:
                    # We have duplicates in the topic tree, make sure the stamping happens to all of them.
                    items = Item.select().where(Item.path == path)
                    for item in items:
                        if item.kind != "Topic":
                            item_data = unparse_model_data(model_to_dict(item, recurse=False))
                            item_data.update(update)
                            item_data = parse_model_data(item_data)
                            for attr, val in item_data.iteritems():
                                setattr(item, attr, val)
                            item.save()
                            recurse_availability_up_tree(item, update.get("available", False))


@set_database
def update_parents(db=None, parent_mapping=None, channel="khan", language="en", **kwargs):
    """
    Convenience function to add parent nodes to other nodes in the database.
    Needs a mapping from item path to parent id.
    As only Topics can be parents, and we can have duplicate ids, we filter on both.
    """

    if parent_mapping:
        with Using(db, [Item]):

            with db.atomic() as transaction:
                for key, value in parent_mapping.iteritems():
                    if value:
                        try:
                            # Only Topics can be parent nodes
                            parent = Item.get(Item.id == value, Item.kind == "Topic")
                            item = Item.get(Item.path == key)
                        except DoesNotExist:
                            print(key, value, "Parent not found" if not parent else "Item not found")
                        if item and parent:
                            item.parent = parent
                            item.save()
