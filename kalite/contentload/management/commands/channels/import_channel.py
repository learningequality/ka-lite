import os
import json
import hashlib
import shutil
import copy

from django.conf import settings; logging = settings.LOG
from django.utils.text import slugify

from functools import partial

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
    "Video": ["kind", "description", "title", "duration", "id", "y_pos", "x_pos", "path", "slug", "organization"],
    "Exercise": ["kind", "description", "title", "name", "id", "y_pos", "x_pos", "path", "slug", "organization"],
    "Audio": ["kind", "description", "title", "id", "y_pos", "x_pos", "path", "slug", "organization"],
    "Document": ["kind", "description", "title", "id", "y_pos", "x_pos", "path", "slug", "organization"],
}

kind_blacklist = [None]

slug_blacklist = []

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = ["x_pos", "y_pos"]

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

def build_full_cache(items, id_key="id"):
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
    """Return list of dictionaries of subdirectories and/or files in the location"""
    # Recursively add all subdirectories
    children = []
    location = location if not location or location[-1] != "/" else location[:-1]
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
    current_path = os.path.join(parent_path, slug)
    try:
        with open(location + ".json", "r") as f:
            meta_data = json.load(f)
    except IOError:
        meta_data = {}
        logging.warning("No metadata for file {base_name}".format(base_name=base_name))
    node = {
        "path": current_path,
        "slug": slug,
    }
    if os.path.isdir(location):
        node.update({
            "kind": "Topic",
            "id": slug,
            "children": sorted([construct_node(os.path.join(location, s), current_path, node_cache, channel) for s in os.listdir(location)], key=lambda x: (not x.get("topic_spotlight", False) if x else True, x.get("title", "") if x else "")),
        })

        node["children"] = [child for child in node["children"] if child]

        node.update(meta_data)

        # Finally, can add contains
        contains = set([])
        for ch in node["children"]:
            contains = contains.union(ch.get("contains", set([])))
            contains = contains.union(set([ch["kind"]]))

        node["contains"] = list(contains)

    else:
        extension = base_name.split(".")[-1]
        kind = file_kind_map.get(extension, None)

        if not kind:
            return None
        elif kind in ["Video", "Audio", "Image"]:
            from kaa import metadata as kaa_metadata
            info = kaa_metadata.parse(location)
            data_meta = {}
            for meta_key, data_fn in file_meta_data_map.items():
                if data_fn(info):
                    data_meta[meta_key] = data_fn(info)
            if data_meta.get("codec", None):
                data_meta["{kind}_codec".format(kind=kind.lower())] = data_meta["codec"]
                del data_meta["codec"]
            data_meta.update(meta_data)
            meta_data = data_meta

        id = file_md5(channel["id"], location)

        node.update({
            "id": id,
            "kind": kind,
            "format": extension,
        })

        node.update(meta_data)

        # Copy over content
        shutil.copy(location, os.path.join(settings.CONTENT_ROOT, id + "." + extension))
        logging.debug("%s file %s to local content directory." % ("Copied", slug))

    # Verify some required fields:
    if "title" not in node:
        logging.warning("Title missing from file {base_name}, using file name instead".format(base_name=base_name))
        if os.path.isdir(location):
            node["title"] = base_name
        else:
            node["title"] = os.path.splitext(base_name)[0]

    # Clean up some fields:
    # allow tags and keywords to be a single item as a string, convert to list
    for key in ["tags", "keywords"]:
        if isinstance(node.get(key, []), basestring):
            node[key] = [node[key]]

    if not os.path.isdir(location):
        nodecopy = copy.deepcopy(node)
        if kind == "Exercise":
            node_cache["Exercise"].append(nodecopy)
        else:
            node_cache["Content"].append(nodecopy)

    return node

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
    }

    topic_tree = construct_node(path, "", node_cache, channel)

    exercises = node_cache["Exercise"]

    assessment_items = []

    content = node_cache["Content"]

    del node_cache["Slugs"]

    annotate_related_content(node_cache)

    return topic_tree, exercises, assessment_items, content

rebuild_topictree = partial(base.rebuild_topictree, whitewash_node_data=whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=channel_data)

def channel_data_files(dest=None):
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
