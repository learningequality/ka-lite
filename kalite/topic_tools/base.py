"""
Important constants and helpful functions for the topic tree and a view on its data, the node cache.

The topic tree is a hierarchical representation of real data (exercises, and videos).
Leaf nodes of the tree are real learning resources, such as videos and exercises.
Non-leaf nodes are topics, which describe a progressively higher-level grouping of the topic data.

Each node in the topic tree comes with lots of metadata, including:
* title
* description
* id (unique identifier; now equivalent to slug below)
* slug (for computing a URL)
* path (which is equivalent to a URL)
* kind (Topic, Exercise, Video)
and more.
"""
import os
import re
import json
import copy
import glob

from django.conf import settings as django_settings
logging = django_settings.LOG

from django.contrib import messages
from django.db import DatabaseError
from django.utils.translation import gettext as _

from fle_utils.general import json_ascii_decoder

from . import settings

CACHE_VARS = []


def database_exists(channel="khan", language="en", database_path=None):
    path = database_path or settings.CONTENT_DATABASE_PATH.format(channel=channel, language=language)

    return os.path.exists(path)

def available_content_databases():
    """
    Generator to return the channel and language for every content database that exists in the system.
    @return: iterator over (channel, language) values
    """
    pattern = re.compile("content_(?P<channel>[^_]+)_(?P<language>[^_]+).sqlite")
    for filename in glob.iglob(django_settings.DEFAULT_DATABASE_DIR):
        match = pattern.search(filename)
        if match:
            yield match.group(1, 2)


def smart_translate_item_data(item_data):
    """Auto translate the content fields of a given assessment item data.

    An assessment item doesn't have the same fields; they change
    depending on the question. Instead of manually specifying the
    fields to translate, this function loops over all fields of
    item_data and translates only the content field.

    """
    # just translate strings immediately
    if isinstance(item_data, basestring):
        return _(item_data)

    elif isinstance(item_data, list):
        return map(smart_translate_item_data, item_data)

    elif isinstance(item_data, dict):
        if 'content' in item_data:
            item_data['content'] = _(item_data['content']) if item_data['content'] else ""

        for field, field_data in item_data.iteritems():
            if isinstance(field_data, dict):
                item_data[field] = smart_translate_item_data(field_data)
            elif isinstance(field_data, list):
                item_data[field] = map(smart_translate_item_data, field_data)

        return item_data
