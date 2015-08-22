"""
Import topic tree from a filesystem source.
"""
import os
import json
import hashlib
import shutil
import copy
import zipfile

from django.conf import settings; logging = settings.LOG
from django.utils.text import slugify

from functools import partial

from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata

import base

slug_key = {
    "Topic": "slug",
    "Video": "slug",
    "Exercise": "slug",
    "AssessmentItem": "slug",
    "Document": "slug",
    "Audio": "slug",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "title",
    "AssessmentItem": "title",
    "Document": "slug",
}

id_key = {
    "Topic": "id",
    "Video": "id",
    "Exercise": "id",
    "AssessmentItem": "id",
    "Document": "id",
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "duration", "id", "path", "slug", "organization"],
    "Exercise": ["kind", "description", "title", "name", "id", "path", "slug", "organization"],
    "Audio": ["kind", "description", "title", "id", "path", "slug", "organization"],
    "Document": ["kind", "description", "title", "id", "path", "slug", "organization"],
}

kind_blacklist = [None]

slug_blacklist = []

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = []

channel_data = {
    "slug_key": slug_key,
    "title_key": title_key,
    "id_key": id_key,
    "iconfilepath": iconfilepath,
    "iconextension":  iconextension,
    "defaulticon": defaulticon,
    "attribute_whitelists": attribute_whitelists,
    "denormed_attribute_list": denormed_attribute_list,
    "kind_blacklist": kind_blacklist,
    "slug_blacklist": slug_blacklist,
    "temp_ok_atts": temp_ok_atts,
}

whitewash_node_data = partial(base.whitewash_node_data, channel_data=channel_data)

def build_full_cache(items):
    """
    Uses list of items retrieved from building the topic tree
    to create an item cache with look up keys.
    """
    return dict((item["id"], item) for item in items)

file_kind_dictionary = {
    "Video": ["mp4", "mov", "3gp", "amv", "asf", "asx", "avi", "mpg", "swf", "wmv"],
    "Image": ["tif", "bmp", "png", "jpg", "jpeg"],
    "Presentation": ["ppt", "pptx"],
    "Spreadsheet": ["xls", "xlsx"],
    "Code": ["html", "js", "css", "py"],
    "Audio": ["mp3", "wma", "wav", "mid", "ogg"],
    "Document": ["pdf", "txt", "rtf", "html", "xml", "doc", "qxd", "docx"],
    "Archive": ["zip", "bzip2", "cab", "gzip", "mar", "tar"],
    "Exercise": ["exercise"],
}

file_kind_map = {}

for key, value in file_kind_dictionary.items():
    for extension in value:
        file_kind_map[extension] = key

file_meta_data_map = {
    "duration": lambda x: getattr(x, "length", None),
    "video_codec": lambda x: getattr(x, "video", [{}])[0].get("codec", None),
    "audio_codec": lambda x: getattr(x, "audio", [{}])[0].get("codec", None),
    "title": lambda x: getattr(x, "title", None),
    "language": lambda x: getattr(x, "langcode", None),
    "keywords": lambda x: getattr(x, "keywords", None),
    "license": lambda x: getattr(x, "copyright", None),
    "codec": lambda x: getattr(x, "codec", None),
}

def file_md5(namespace, file_path):
    m = hashlib.md5()
    m.update(namespace)
    with open(file_path, "r") as f:
        while True:
            chunk = f.read(128)
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest()

def construct_node(location, parent_path, node_cache, channel):
    """
    Return list of dictionaries of subdirectories and/or files in the location.
    If location is a directory, this will be called recursively on every file and subdirectory within, creating nodes
        for each item and attaching them as children to the node corresponding to the containing directory.

    :param location: A string. Path to node data to be imported. Depending on the extension, a different node
        will be returned -- directories will create a Topic node, and different extensions will create nodes based on
        the extension's value as a key in the module-defined dict `file_kind_map`. Files with the .json extension are
        ignored as nodes -- but they can be used to add metadata to any arbitrary file. Extensions without an entry in
        `file_kind_map` return None.
    :param parent_path: A string. The directory corresponding to the parent Topic node.
    :param node_cache: A mutable object, which will be updated with node data.
    :param channel: A channel dictionary. Should at least have keys "name" and "id".
    :return: None if location ends with `.json` or is not found in `file_kind_map`. Otherwise a dictionary.
    """
    location = location if not location else os.path.realpath(location)
    base_name = os.path.basename(location)
    if base_name.endswith(".json"):
        return None
    if not parent_path:
        base_name = channel["name"]

    slug = slugify(unicode(".".join(base_name.split(".")[:-1])))
    if not slug or slug in node_cache["Slugs"]:
        slug = slugify(unicode(base_name))
    # Note: It is assumed that any file with *exactly* the same file name is the same file.
    node_cache["Slugs"].add(slug)

    meta_data = get_metadata_or_none(location)  # Could be updated depending on node type

    current_path = os.path.join(parent_path, slug)
    node = {
        "path": current_path,
        "slug": slug,
    }

    # If location is a directory, add a topic node. If not, add a kind of node depending on the extension.
    if os.path.isdir(location):
        node.update({
            "kind": "Topic",
            "id": slug,
            "children": [construct_node(os.path.join(location, s), current_path, node_cache, channel) for s in
                         os.listdir(location)],
        })
        sort_key = lambda x: (not x.get("topic_spotlight", False) if x else True, x.get("title", "") if x else "")
        node["children"] = sorted([child for child in node["children"] if child], key=sort_key)

        # Finally, can add contains
        contains = set([])
        for ch in node["children"]:
            contains = contains.union(ch.get("contains", set([])))
            contains = contains.union(set([ch["kind"]]))

        node["contains"] = list(contains)

    else:
        extension = base_name.split(".")[-1]
        kind = file_kind_map.get(extension, None)
        if kind:
            node.update({
                "id": file_md5(channel["id"], location),
                "kind": kind,
            })
        else:
            return None

        if kind in ["Video", "Audio", "Image"]:
            node, extra_meta_data = construct_media_node_bundle(node, extension, location)
            extra_meta_data.update(meta_data)
            meta_data = extra_meta_data

        elif kind == "Exercise":
            extra_meta_data, assessment_items = construct_exercise_bundle(location, channel)
            meta_data.update(extra_meta_data)

    node.update(meta_data)
    node = clean_up_node(node, location)

    if node["kind"] != "Topic":
        nodecopy = copy.deepcopy(node)
        if node["kind"] == "Exercise":
            node_cache["Exercise"].append(nodecopy)
            node_cache["AssessmentItem"].extend(assessment_items)
        else:
            node_cache["Content"].append(nodecopy)

    return node


def construct_exercise_bundle(location, channel):
    """
    Construct a bundle for an exercise node, which should be a special zipfile.

    :param location: A string. The node's location, a la construct_node. Should be a zipfile.
    :param channel: The channel dictionary, a la construct_node. Requires the "name" item.
    :return: A tuple (extra_meta_data, assessment_items).
        extra_meta_data: A dict. Extracted meta data from "exercise.json" if it exists.
        assessment_items: A list. Assessment items from "assessment_items.json" if they're included.
    """
    zf = zipfile.ZipFile(open(location, "rb"), "r")

    try:
        extra_meta_data = json.loads(zf.read("exercise.json"))
    except KeyError:
        extra_meta_data = {}
        logging.debug("No exercise metadata available in zipfile")

    try:
        assessment_items = json.loads(zf.read("assessment_items.json"))
    except KeyError:
        assessment_items = []
        logging.debug("No assessment items found in zipfile")
    for filename in zf.namelist():
        if os.path.splitext(filename)[0] != "json":
            zf.extract(filename, os.path.join(settings.ASSESSMENT_ITEM_ROOT, channel["name"]))

    return extra_meta_data, assessment_items


def construct_media_node_bundle(node, extension, location):
    """
    Given a bunch of parameters, returns an updated node and meta data (extra_meta_data).
    Copies files from "location" to settings.CONTENT_ROOT.

    :param node: A dict. The node -- will be changed in place.
    :param extension: A string. The file extension.
    :param location: A string. The node's location, a la construct_node.
    :return: A tuple, (node, extra_meta_data).
        node: A dict. The updated node.
        extra_meta_data: A dict. Extra meta data extracted from the file.
    """
    node.update({
        "format": extension,
    })

    shutil.copy(location, os.path.join(settings.CONTENT_ROOT, node["id"] + "." + extension))
    logging.debug("Copied file %s to local content directory." % node["slug"])

    extra_meta_data = {}
    filename = unicodeFilename(location)
    parser = createParser(filename, location)
    if parser:
        info = extractMetadata(parser)
        for meta_key, data_fn in file_meta_data_map.items():
            if data_fn(info):
                extra_meta_data[meta_key] = data_fn(info)
        if extra_meta_data.get("codec", None):
            extra_meta_data["{kind}_codec".format(kind=node["kind"].lower())] = extra_meta_data["codec"]
            del extra_meta_data["codec"]

    return node, extra_meta_data


def clean_up_node(node, location):
    """
    Ensure node has a title and fold together certain attributes

    :param node: A dict. The almost-finished node to be cleaned up.
    :param location: A string. The location (a la construct_node) that the node is constructed from.
    :return: The cleaned-up node.
    """
    base_name = os.path.basename(location)
    if "title" not in node:
        logging.warning("Title missing from file {base_name}, using file name instead".format(base_name=base_name))
        if os.path.isdir(location):
            node["title"] = base_name
        else:
            node["title"] = os.path.splitext(base_name)[0]

    # Clean up some fields:
    # allow tags and keywords to be a single item as a string, convert to list
    for key in ["tags", "keywords"]:
        if isinstance(node.get(key), basestring):
            node[key] = [node[key]]
    return node


def get_metadata_or_none(location):
    """
    Reads and returns json metadata if it exists at "location".

    :param location: path to node data. Metadata should be in the file location+".json"
    :return: The metadata if no IOError is raised, or else an empty dict.
    """
    try:
        with open(location + ".json", "r") as f:
            meta_data = json.load(f)
    except IOError:
        meta_data = {}
        logging.warning("No metadata for file: {location}".format(location=location))
    return meta_data


path = ""

channel_data_path = None

def annotate_related_content(node_cache):

    slug_cache = {}

    for cache in node_cache.values():
        for item in cache:
            slug_cache[item.get("slug")] = item

    for cache in node_cache.values():
        for item in cache:
            # allow related_content to be a single item as a string
            if isinstance(item.get("related_content", []), basestring):
                item["related_content"] = [item["related_content"]]
            # or a list of several related items
            for i, related_item in enumerate(item.get("related_content", [])):
                content = slug_cache.get(slugify(unicode(related_item.split(".")[0])))
                if content:
                    item["related_content"][i] = {
                        "id": content.get("id"),
                        "kind": content.get("kind"),
                        "path": content.get("path"),
                        "title": content.get("title"),
                    }
                else:
                    item["related_content"][i] = None
            if item.get("related_content", []):
                item["related_content"] = [related_item for related_item in item["related_content"] if related_item]
                if not item["related_content"]:
                    del item["related_content"]


def retrieve_API_data(channel=None):

    if not os.path.isdir(path):
        raise Exception("The specified path is not a valid directory")

    node_cache = {
        "Exercise": [],
        "Content": [],
        "Slugs": set(),
        "AssessmentItem": [],
    }

    topic_tree = construct_node(path, "", node_cache, channel)
    exercises = node_cache["Exercise"]
    assessment_items = node_cache["AssessmentItem"]
    content = node_cache["Content"]

    del node_cache["Slugs"]

    annotate_related_content(node_cache)

    return topic_tree, exercises, assessment_items, content

rebuild_topictree = partial(base.rebuild_topictree, whitewash_node_data=whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=channel_data)

def channel_data_files(dest=None):
    """
    Copies all remaining files to appropriate channel data directory
    """
    channel_data_filename = "channel_data.json"
    if dest:
        if not channel_data_path:
            sourcedir = os.path.dirname(path)
            sourcefile = os.path.basename(path) + ".json" if os.path.exists(os.path.basename(path) + ".json") else channel_data_filename
        else:
            sourcedir = channel_data_path
            sourcefile = channel_data_filename
        shutil.copy(os.path.join(sourcedir, sourcefile), os.path.join(dest, channel_data_filename))
        shutil.rmtree(os.path.join(dest, "images"), ignore_errors=True)
        shutil.copytree(os.path.join(sourcedir, "images"), os.path.join(dest, "images"))
