"""
Utilities for downloading Khan Academy topic tree and 
massaging into data and files that we use in KA Lite.
"""

import copy
import json
import os
import requests
import shutil
import sys

from django.core.management.base import BaseCommand, CommandError

import settings
from utils.topics import slug_key, title_key, topics_file, node_cache_file, map_layout_file

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "v_position", "h_position"]
}

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

kind_slugs = {
    "Video": "v/",
    "Exercise": "e/",
    "Topic": ""
}

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res"]


def download_khan_data(url, debug_cache_file=None):
    if not debug_cache_file:
        debug_cache_file = url.split("/")[-1] + ".json"

    if not os.path.exists("json"):
        os.mkdir("json")
    debug_cache_file = os.path.join("json", debug_cache_file)

    if settings.DEBUG and os.path.exists(debug_cache_file):
        # Slow to debug, so keep a local cache in the debug case only.
        sys.stdout.write("Using cached file: %s\n" % debug_cache_file)
        data = json.loads(open(debug_cache_file).read())
    else:
        sys.stdout.write("Downloading data from %s..." % url)
        sys.stdout.flush()
        data = json.loads(requests.get(url).content)
        sys.stdout.write("done.\n")
        if settings.DEBUG:
            with open(debug_cache_file, "w") as fh:
                fh.write(json.dumps(data))
    return data

def refresh_topictree(data_path=settings.PROJECT_PATH + "/static/data/", remove_unknown_exercises=False):
    knowledge_topics = {}

    topics = download_khan_data("http://www.khanacademy.org/api/v1/topictree")
    knowledge_map = download_khan_data("http://www.khanacademy.org/api/v1/maplayout")

    related_exercise = {}

    def recurse_nodes(node, path=""):

        kind = node["kind"]

        # Only keep key data we can use
        keys_to_delete = []
        for key in node:
            if key not in attribute_whitelists[kind]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del node[key]

        # Fix up data
        try:
            node["slug"] = node[slug_key[kind]]
            if node["slug"] == "root":
                node["slug"] = ""
        except KeyError:
            print node.keys()
        node["title"] = node[title_key[kind]]
        node["path"] = path + kind_slugs[kind] + node["slug"] + "/"

        kinds = set([kind])

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

        if kind == "Topic":
            node["contains"] = list(kinds)

        return kinds

    def recurse_nodes_to_add_related_exercise(node):
        if node["kind"] == "Video":
            node["related_exercise"] = related_exercise.get(node["slug"], None)
        for child in node.get("children", []):
            recurse_nodes_to_add_related_exercise(child)

    def find_all_exercises(node):
        exercises = []
        if node["kind"] == "Exercise":
            exercises.append(node)
        for child in node.get("children", []):
            if child["kind"] == "Exercise":
                exercises.append(child)
            elif child["kind"] == "Topic":
                exercises.extend(find_all_exercises(child))
        return exercises

    def recurse_nodes_to_extract_knowledge_map(node):
        if "contains" in node:
            if "Exercise" in node["contains"]:
                try:
                    if node["in_knowledge_map"]:
                        if node["node_slug"] not in knowledge_map["topics"]:
                            print node["node_slug"]
                        knowledge_topics[node["node_slug"]] = find_all_exercises(node)
                    else:
                        for child in node.get("children", []):
                            recurse_nodes_to_extract_knowledge_map(child)
                except KeyError:
                    for child in node.get("children", []):
                        recurse_nodes_to_extract_knowledge_map(child)

    # Download icons
    for key, value in knowledge_map["topics"].items():
        if "icon_url" in value:
            value["icon_url"] = iconfilepath + value["id"] + iconextension
            knowledge_map["topics"][key] = value

            out_path = data_path + "../" + value["icon_url"]
            if not os.path.exists(out_path):
                icon = requests.get("http://www.khanacademy.org" + value["icon_url"])
                if icon.status_code == 200:
                    iconfile = file(data_path + "../" + value["icon_url"], "w")
                    iconfile.write(icon.content)
                else:
                    value["icon_url"] = iconfilepath + defaulticon + iconextension


    # Limit exercises to only the previous list
    def recurse_nodes_to_delete_exercise(node, OLD_NODE_CACHE):
        if node["kind"] == "Topic":
            children_to_delete = []
            for ci, child in enumerate(node.get("children", [])):
                if child["kind"] == "Exercise":
                    if not child["slug"] in OLD_NODE_CACHE["Exercise"].keys():
                        children_to_delete.append(ci)
                elif child.get("children",None):
                    recurse_nodes_to_delete_exercise(child, OLD_NODE_CACHE)
                    # Delete children without children (all their children were removed)
                    if not child.get("children",None):
                        children_to_delete.append(ci)
            for i in reversed(children_to_delete):
                settings.LOG.debug("Deleting unknown exercise %s" % node["children"][i]["slug"])
                del node["children"][i]

    recurse_nodes(topics)
    if remove_unknown_exercises:
        OLD_NODE_CACHE = json.loads(open(os.path.join(data_path, node_cache_file)).read())
        recurse_nodes_to_delete_exercise(topics, OLD_NODE_CACHE)
    recurse_nodes_to_add_related_exercise(topics)
    recurse_nodes_to_extract_knowledge_map(topics)

    with open(os.path.join(data_path, topics_file), "w") as fp:
        fp.write(json.dumps(topics, indent=2))

    with open(os.path.join(data_path, map_layout_file), "w") as fp:
        fp.write(json.dumps(knowledge_map, indent=2))

    # Rewrite topicdata, obliterating the old (to remove cruft)
    topicdata_dir = os.path.join(data_path, "topicdata")
    shutil.rmtree(topicdata_dir)
    os.mkdir(topicdata_dir)
    for key, value in knowledge_topics.items():
        with open(os.path.join(topicdata_dir, "%s.json" % key), "w") as fp:
            fp.write(json.dumps(value, indent=2))





def generate_node_cache(output_dir=settings.DATA_PATH):
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

    recurse_nodes(json.loads(open(os.path.join(output_dir, topics_file)).read()))

    with open(os.path.join(output_dir, node_cache_file), "w") as fp:
        fp.write(json.dumps(node_cache, indent=2))

    sys.stdout.write("Downloaded %d topics, %d videos, %d exercises\n" % (
        len(node_cache["Topic"]),
        len(node_cache["Video"]),
        len(node_cache["Exercise"]),
    ))



def create_youtube_id_to_slug_map(data_path=settings.PROJECT_PATH + "/static/data/"):
    """Go through all videos, and make a map of youtube_id to slug, for fast look-up later"""

    map_file = data_path + "youtube_to_slug_map.json"

    if not os.path.exists(map_file):
        NODE_CACHE = json.loads(open(data_path + "nodecache.json").read())
        ID2SLUG_MAP = dict()

        # Make a map from youtube ID to video slug
        for v in NODE_CACHE['Video'].values():
            ID2SLUG_MAP[v['youtube_id']] = v['slug']

        # Save the map!
        with open(map_file, "w") as fp:
            fp.write(json.dumps(ID2SLUG_MAP, indent=2))




class Command(BaseCommand):
    help = """**WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches from Khan Academy.
    Options:
        [no args] - download from Khan Academy and refresh all files
        id2slug - regenerate the id2slug map file.
"""

    def handle(self, *args, **options):
        if len(args) == 0:
            refresh_topictree(remove_unknown_exercises=True)
            generate_node_cache()
            create_youtube_id_to_slug_map()

        elif args[0] == "id2slug":
            create_youtube_id_to_slug_map()

        else:
            raise CommandError("Unknown argument list: %s" % args)