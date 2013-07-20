"""
Utilities for downloading Khan Academy topic tree and 
massaging into data and files that we use in KA Lite.
"""

import copy
import datetime
import json
import os
import requests
import shutil
import sys
import time

from django.core.management.base import BaseCommand, CommandError

import settings
from settings import LOG as logging
from utils.general import datediff
from utils import topic_tools


slug_key = {
    "Topic": "node_slug",
    "Video": "readable_id",
    "Exercise": "name",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "v_position", "h_position"]
}

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res"]


def download_khan_data(url, debug_cache_file=None, debug_cache_dir="json"):
    """
    Download data from the given url.
    
    In DEBUG mode, these downloads are slow.  So for the sake of faster iteration,
    save the download to disk and re-serve it up again, rather than download again,
    if the file is less than a day old.
    """

    # Get the filename
    if not debug_cache_file:
        debug_cache_file = url.split("/")[-1] + ".json"

    # Create a directory to store these cached json files 
    if not os.path.exists(debug_cache_dir):
        os.mkdir(debug_cache_dir)
    debug_cache_file = os.path.join(debug_cache_dir, debug_cache_file)

    # Use the cache file if:
    # a) We're in DEBUG mode
    # b) The debug cache file exists
    # c) It's less than a day old.
    if settings.DEBUG and os.path.exists(debug_cache_file) and datediff(datetime.datetime.now(), datetime.datetime.fromtimestamp(os.path.getctime(debug_cache_file)), units="days") <= 7.0:
        # Slow to debug, so keep a local cache in the debug case only.
        sys.stdout.write("Using cached file: %s\n" % debug_cache_file)
        data = json.loads(open(debug_cache_file).read())
    else:
        sys.stdout.write("Downloading data from %s..." % url)
        sys.stdout.flush()
        data = json.loads(requests.get(url).content)
        sys.stdout.write("done.\n")
        # In DEBUG mode, store the debug cache file.
        if settings.DEBUG:
            with open(debug_cache_file, "w") as fh:
                fh.write(json.dumps(data))
    return data


def rebuild_topictree(data_path=settings.PROJECT_PATH + "/static/data/", remove_unknown_exercises=False):
    """
    Downloads topictree (and supporting) data from Khan Academy and uses it to
    rebuild the KA Lite topictree cache (topics.json).
    """

    topictree = download_khan_data("http://www.khanacademy.org/api/v1/topictree")

    related_exercise = {}  # Temp variable to save exercises related to particular videos

    def recurse_nodes(node, path=""):
        """
        Internal function for recursing over the topic tree, marking relevant metadata,
        and removing undesired attributes and children.
        """
        
        kind = node["kind"]

        # Only keep key data we can use
        keys_to_delete = []
        for key in node:
            if key not in attribute_whitelists[kind]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del node[key]

        # Fix up data
        if slug_key[kind] not in node:
            logging.warn("Could not find expected slug key (%s) on node: %s" % (slug_key[kind], node))
        else:
            node["slug"] = node[slug_key[kind]]
            if node["slug"] == "root":
                node["slug"] = ""
        node["title"] = node[title_key[kind]]
        node["path"] = path + topic_tools.kind_slugs[kind] + node["slug"] + "/"
        node["id"] = node["slug"]  # these used to be the same; now not. Easier if they stay the same (issue #233)

        kinds = set([kind])

        # For each exercise, need to get related videos
        if kind == "Exercise":
            related_video_readable_ids = [vid["readable_id"] for vid in download_khan_data("http://www.khanacademy.org/api/v1/exercises/%s/videos" % node["name"], node["name"] + ".json")]
            node["related_video_readable_ids"] = related_video_readable_ids
            exercise = {
                "slug": node[slug_key[kind]],
                "title": node[title_key[kind]],
                "path": node["path"],
            }
            for video_id in node.get("related_video_readable_ids", []):
                related_exercise[video_id] = exercise

        # Recurse through children, remove any blacklisted items
        children_to_delete = []
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)
            if child_kind in kind_blacklist:
                children_to_delete.append(i)
                continue
            if child[slug_key[child_kind]] in slug_blacklist:
                children_to_delete.append(i)
                continue
            kinds = kinds.union(recurse_nodes(child, node["path"]))
        for i in reversed(children_to_delete):
            del node["children"][i]

        # Mark on topics whether they contain Videos, Exercises, or both
        if kind == "Topic":
            node["contains"] = list(kinds)

        return kinds


    def recurse_nodes_to_add_related_exercise(node):
        """
        Internal function for recursing the topic tree and marking related exercises.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        if node["kind"] == "Video":
            node["related_exercise"] = related_exercise.get(node["slug"], None)
        for child in node.get("children", []):
            recurse_nodes_to_add_related_exercise(child)


    # Limit exercises to only the previous list
    def recurse_nodes_to_delete_exercise(node, OLD_NODE_CACHE):
        """
        Internal function for recursing the topic tree and removing new exercises.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        # Stop recursing when we hit leaves
        if node["kind"] != "Topic":
            return

        children_to_delete = []
        for ci, child in enumerate(node.get("children", [])):
            # Mark all unrecognized exercises for deletion
            if child["kind"] == "Exercise":
                if not child["slug"] in OLD_NODE_CACHE["Exercise"].keys():
                    children_to_delete.append(ci)
            # Recurse over children to delete
            elif child.get("children", None):
                recurse_nodes_to_delete_exercise(child, OLD_NODE_CACHE)
                # Delete children without children (all their children were removed)
                if not child.get("children", None):
                    children_to_delete.append(ci)

        # Do the actual deletion
        for i in reversed(children_to_delete):
            logging.debug("Deleting unknown exercise %s" % node["children"][i]["slug"])
            del node["children"][i]

    recurse_nodes(topictree)
    if remove_unknown_exercises:
        OLD_NODE_CACHE = topic_tools.get_node_cache()
        recurse_nodes_to_delete_exercise(topictree, OLD_NODE_CACHE)
    recurse_nodes_to_add_related_exercise(topictree)

    with open(os.path.join(data_path, topic_tools.topics_file), "w") as fp:
        fp.write(json.dumps(topictree, indent=2))

    return topictree


def rebuild_knowledge_map(topictree, data_path=settings.PROJECT_PATH + "/static/data/", force_icons=False):

    """
    Uses KA Lite topic data and supporting data from Khan Academy 
    to rebuild the knowledge map (maplayout.json) and topicdata files.
    """

    knowledge_map = download_khan_data("http://www.khanacademy.org/api/v1/maplayout")
    knowledge_topics = {}  # Stored variable that keeps all exercises related to second-level topics

    # Download icons
    for key, value in knowledge_map["topics"].items():
        if "icon_url" in value:
            # Note: id here is retrieved from knowledge_map, so we're OK
            #   that we blew away ID in the topic tree earlier.
            value["icon_url"] = iconfilepath + value["id"] + iconextension
            knowledge_map["topics"][key] = value

            out_path = data_path + "../" + value["icon_url"]
            if not os.path.exists(out_path) or force_icons:
                icon_khan_url = "http://www.khanacademy.org" + value["icon_url"]
                sys.stdout.write("Downloading icon %s from %s..." % (value["id"], icon_khan_url))
                sys.stdout.flush()
                icon = requests.get(icon_khan_url)
                if icon.status_code == 200:
                    iconfile = file(data_path + "../" + value["icon_url"], "w")
                    iconfile.write(icon.content)
                else:
                    sys.stdout.write(" [NOT FOUND]")
                    value["icon_url"] = iconfilepath + defaulticon + iconextension
                sys.stdout.write(" done.\n")

    def recurse_nodes_to_extract_knowledge_map(node):
        """
        Internal function for recursing the topic tree and building the knowledge map.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        if "contains" not in node or "Exercise" not in node["contains"]:
            return

        if node.get("in_knowledge_map", None):
            if node["slug"] not in knowledge_map["topics"]:
                logging.debug("Not in knowledge map: %s" % node["slug"])
            knowledge_topics[node["slug"]] = topic_tools.get_topic_exercises(node["slug"])
        else:
            for child in node.get("children", []):
                recurse_nodes_to_extract_knowledge_map(child)
    recurse_nodes_to_extract_knowledge_map(topictree)

    # Dump the knowledge map
    with open(os.path.join(data_path, topic_tools.map_layout_file), "w") as fp:
        fp.write(json.dumps(knowledge_map, indent=2))

    # Rewrite topicdata, obliterating the old (to remove cruft)
    topicdata_dir = os.path.join(data_path, "topicdata")
    if os.path.exists(topicdata_dir):
        shutil.rmtree(topicdata_dir)
        os.mkdir(topicdata_dir)
    for key, value in knowledge_topics.items():
        with open(os.path.join(topicdata_dir, "%s.json" % key), "w") as fp:
            fp.write(json.dumps(value, indent=2))

    return knowledge_topics


def generate_node_cache(topictree=None, output_dir=settings.DATA_PATH):
    """
    Given the KA Lite topic tree, generate a dictionary of all Topic, Exercise, and Video nodes.
    """

    if not topictree:
        topictree = topic_tools.get_topic_tree(force=True)
    node_cache = {}

    def recurse_nodes(node, path="/"):
        # Add the node to the node cache
        kind = node["kind"]
        node_cache[kind] = node_cache.get(kind, {})
        if node["slug"] not in node_cache[kind]:
            # New node, so copy off, massage, and store.
            node_copy = copy.copy(node)
            if "children" in node_copy:
                del node_copy["children"]
            node_cache[kind][node["slug"]] = node_copy
        for child in node.get("children", []):
            recurse_nodes(child, node["path"])
    recurse_nodes(topictree)

    with open(os.path.join(output_dir, topic_tools.node_cache_file), "w") as fp:
        fp.write(json.dumps(node_cache, indent=2))

    return node_cache


def create_youtube_id_to_slug_map(node_cache=None, data_path=settings.PROJECT_PATH + "/static/data/"):
    """
    Go through all videos, and make a map of youtube_id to slug, for fast look-up later
    """

    if not node_cache:
        node_cache = topic_tools.get_node_cache(force=True)

    map_file = os.path.join(data_path, topic_tools.video_remap_file)
    id2slug_map = dict()

    # Make a map from youtube ID to video slug
    for v in node_cache['Video'].values():
        assert v["youtube_id"] not in id2slug_map, "Make sure there's a 1-to-1 mapping between youtube_id and slug"
        id2slug_map[v['youtube_id']] = v['slug']

    # Save the map!
    with open(map_file, "w") as fp:
        fp.write(json.dumps(id2slug_map, indent=2))


class Command(BaseCommand):
    help = """**WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches from Khan Academy.
    Options:
        [no args] - download from Khan Academy and refresh all files
        id2slug - regenerate the id2slug map file.
"""

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Unknown argument list: %s" % args)

        # TODO(bcipolli)
        # Make remove_unknown_exercises and force_icons into command-line arguments
        topictree = rebuild_topictree(remove_unknown_exercises=True)
        rebuild_knowledge_map(topictree, force_icons=True)

        node_cache = generate_node_cache(topictree)
        create_youtube_id_to_slug_map(node_cache)

        sys.stdout.write("Downloaded topictree data for %d topics, %d videos, %d exercises\n" % (
            len(node_cache["Topic"]),
            len(node_cache["Video"]),
            len(node_cache["Exercise"]),
        ))
