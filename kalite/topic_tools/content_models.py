import os
import json

from django.conf import settings as django_settings

import sqlite3

from peewee import Model, SqliteDatabase, CharField, TextField, BooleanField, ForeignKeyField, PrimaryKeyField, Using, DoesNotExist, fn
from playhouse.shortcuts import model_to_dict

from .settings import CONTENT_DATABASE_PATH
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
    id = CharField(index=True, unique=True)
    pk = PrimaryKeyField(primary_key=True)
    slug = CharField()
    path = CharField(index=True)
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

        path = kwargs.pop("database_path", None) or CONTENT_DATABASE_PATH.format(channel=kwargs.get("channel", "khan"), language=language)

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
def get_content_item(content_id=None, db=None, **kwargs):
    """
    Convenience function for returning a fully fleshed out content node for use in rendering content
    To save server processing, the extra_fields are fleshed out on the client side.
    """
    if content_id:
        with Using(db, [Item]):
            value = Item.get(Item.id == content_id)
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


@set_database
def get_topic_nodes(parent=None, db=None, **kwargs):
    """
    Convenience function for returning a set of topic nodes with limited fields for rendering the topic tree
    """
    if parent:
        with Using(db, [Item]):
            Parent = Item.alias()
            if parent == "root":
                selector = Parent.parent.is_null()
            else:
                selector = Parent.id == parent
            values = [item for item in Item.select(
                Item.title,
                Item.description,
                Item.available,
                Item.kind,
                Item.children,
                Item.id,
                Item.path,
                Item.slug,
                ).join(Parent, on=(Item.parent == Parent.pk)).where(selector).dicts()]
            return values


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

            return Item.select(
                Item
                ).where(Item.kind.in_(kinds), Item.path.contains(topic_node.path))


@set_database
def search_topic_nodes(kinds=None, query=None, db=None, **kwargs):
    if query:
        with Using(db, [Item]):
            if not kinds:
                kinds = ["Video", "Audio", "Exercise", "Document", "Topic"]
            try:
                topic_node = Item.get(fn.Lower(Item.title) == query, Item.kind.in_(kinds))
                return [model_to_dict(topic_node)], True
            except DoesNotExist:
                # For efficiency, don't do substring matches when we've got lots of results
                topic_nodes = Item.select().where((Item.kind.in_(kinds)) & ((fn.Lower(Item.title).contains(query)) | (fn.Lower(Item.extra_fields).contains(query)))).dicts()
                return topic_nodes, False


@set_database
def bulk_insert(items, db=None, **kwargs):
    if items:
        with Using(db, [Item]):
            with db.atomic():
                for idx in range(0, len(items), 500):
                    Item.insert_many(map(parse_model_data, items[idx:idx+500])).execute()


@set_database
def get_or_create(item, db=None, **kwargs):
    if item:
        with Using(db, [Item]):
            Item.get_or_create(parse_model_data(item))


@set_database
def update(update=None, select=None, **kwargs):
    if update:
        with Using(db, [Item]):
            if select:
                query = Item.update(**update).select(select)
            else:
                query = Item.update(**update)

            query.execute()


@set_database
def create_table(db=None, **kwargs):
    with Using(db, [Item]):
        db.create_tables([Item])


@set_database
def annotate_content_models(db=None, channel="khan", language="en", ids=None, **kwargs):
    content_models = get_content_items(ids=ids, channel=channel, language=language)
    updates_dict = update_content_availability(content_models)

    for key, value in updates_dict.iteritems():
        updates_dict[key] = parse_model_data(value)

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


            for id, update in updates_dict.iteritems():
                if update:
                    item = Item.get(id=id)
                    for attr, val in update.iteritems():
                        setattr(item, attr, val)
                    item.save()
                    recurse_availability_up_tree(item, update.get("available", False))


@set_database
def update_parents(db=None, parent_mapping=None, channel="khan", language="en", **kwargs):

    if parent_mapping:
        with Using(db, [Item]):

            with db.atomic() as transaction:
                for key, value in parent_mapping.iteritems():
                    if value:
                        parent_id = Item.get(id=value).pk
                        item = Item.get(id=key)
                        item.parent = parent_id
                        item.save()
