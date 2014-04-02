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
from math import ceil, log, exp  # needed for basepoints calculation
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError

from ... import KHANLOAD_CACHE_DIR, kind_slugs
from fle_utils.general import datediff
from kalite.main import topic_tools


# get the path to an exercise file, so we can check, below, which ones exist
EXERCISE_FILEPATH_TEMPLATE = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s.html")

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

id_key = {
    "Topic": "node_slug",
    "Video": "youtube_id",
    "Exercise": "name",
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

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res", "MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "cs", "cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math", "cc-seventh-grade-math", "cc-eighth-grade-math", "hour-of-code"]

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = ["x_pos", "y_pos", "in_knowledge_map", "icon_src", u'topic_page_url', u'hide', "live", "node_slug", "extended_slug"]


def download_khan_data(url, debug_cache_file=None, debug_cache_dir=KHANLOAD_CACHE_DIR):
    """Download data from the given url.

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
    data = None

    # Use the cache file if:
    # a) We're in DEBUG mode
    # b) The debug cache file exists
    # c) It's less than 7 days old.
    if settings.DEBUG and os.path.exists(debug_cache_file) and datediff(datetime.datetime.now(), datetime.datetime.fromtimestamp(os.path.getctime(debug_cache_file)), units="days") <= 1E6:
        # Slow to debug, so keep a local cache in the debug case only.
        #sys.stdout.write("Using cached file: %s\n" % debug_cache_file)
        try:
            with open(debug_cache_file, "r") as fp:
                data = json.load(fp)
        except Exception as e:
            sys.stderr.write("Error loading cached document %s: %s\n" % (debug_cache_file, e))

    if data is None:  # Failed to get a cached copy
        sys.stdout.write("Downloading data from %s..." % url)
        sys.stdout.flush()
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = json.loads(response.content)
            sys.stdout.write("done.\n")
        except requests.HTTPError as e:
            sys.stderr.write("Error downloading %s: %s\n" % (url, e))
            return None

        # In DEBUG mode, store the debug cache file.
        if settings.DEBUG:
            with open(debug_cache_file, "w") as fh:
                fh.write(json.dumps(data))

    return data


def rebuild_topictree(remove_unknown_exercises=False, remove_disabled_topics=True):
    """Downloads topictree (and supporting) data from Khan Academy and uses it to
    rebuild the KA Lite topictree cache (topics.json).
    """

    topic_tree = download_khan_data("http://www.khanacademy.org/api/v1/topictree?kind=Video,Exercise")

    related_exercise = {}  # Temp variable to save exercises related to particular videos
    related_videos = {}  # Similar idea, reverse direction

    def recurse_nodes(node, path="", ancestor_ids=[]):
        """
        Internal function for recursing over the topic tree, marking relevant metadata,
        and removing undesired attributes and children.
        """

        kind = node["kind"]

        # Only keep key data we can use
        for key in node.keys():
            if key not in attribute_whitelists[kind]:
                del node[key]

        # Fix up data
        if slug_key[kind] not in node:
            logging.warn("Could not find expected slug key (%s) on node: %s" % (slug_key[kind], node))
            node[slug_key[kind]] = node["id"]  # put it SOMEWHERE.
        node["slug"] = node[slug_key[kind]] if node[slug_key[kind]] != "root" else ""
        node["id"] = node[id_key[kind]]  # these used to be the same; now not. Easier if they stay the same (issue #233)

        node["path"] = path + kind_slugs[kind] + node["slug"] + "/"
        node["title"] = node[title_key[kind]].strip()

        # Add some attribute that should have been on there to start with.
        node["parent_id"] = ancestor_ids[-1] if ancestor_ids else None
        node["ancestor_ids"] = ancestor_ids

        if kind == "Exercise":
            # For each exercise, need to set the exercise_id
            #   get related videos
            #   and compute base points
            node["exercise_id"] = node["slug"]

            # compute base points
            # Minimum points per exercise: 5
            node["basepoints"] = ceil(7 * log(max(exp(5./7), node["seconds_per_fast_problem"])));

            # Related videos
            vids = download_khan_data("http://www.khanacademy.org/api/v1/exercises/%s/videos" % node["name"], node["name"] + ".json")
            node["related_video_slugs"] = [vid["readable_id"] for vid in vids] if vids else []

            related_exercise_metadata = {
                "id": node["id"],
                "slug": node["slug"],
                "title": node["title"],
                "path": node["path"],
            }
            for video_slug in node.get("related_video_slugs", []):
                related_exercise[video_slug] = related_exercise_metadata


        # Recurse through children, remove any blacklisted items
        children_to_delete = []
        child_kinds = set()
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)

            # Blacklisted--remove
            if child_kind in kind_blacklist:
                children_to_delete.append(i)
                continue
            elif child[slug_key[child_kind]] in slug_blacklist:
                children_to_delete.append(i)
                continue
            elif not child.get("live", True) and remove_disabled_topics:  # node is not live
                logging.debug("Remvong non-live child: %s" % child[slug_key[child_kind]])
                children_to_delete.append(i)
                continue
            elif child.get("hide", False) and remove_disabled_topics:  # node is hidden. Note that root is hidden, and we're implicitly skipping that.
                children_to_delete.append(i)
                logging.debug("Remvong hidden child: %s" % child[slug_key[child_kind]])
                continue
            elif child_kind == "Video" and set(["mp4", "png"]) - set(child.get("download_urls", {}).keys()):
                # for now, since we expect the missing videos to be filled in soon,
                #   we won't remove these nodes
                sys.stderr.write("WARNING: No download link for video: %s: authors='%s'\n" % (child["youtube_id"], child["author_names"]))
                children_to_delete.append(i)
                continue

            child_kinds = child_kinds.union(set([child_kind]))
            child_kinds = child_kinds.union(recurse_nodes(child, path=node["path"], ancestor_ids=ancestor_ids + [node["id"]]))

        # Delete those marked for completion
        for i in reversed(children_to_delete):
            del node["children"][i]

        # Mark on topics whether they contain Videos, Exercises, or both
        if kind == "Topic":
            node["contains"] = list(child_kinds)

        return child_kinds
    recurse_nodes(topic_tree)


    def recurse_nodes_to_clean_related_videos(node):
        """
        Internal function for recursing the topic tree and marking related exercises.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        def get_video_node(video_slug, node):
            if node["kind"] == "Topic":
                for child in node.get("children", []):
                    video_node = get_video_node(video_slug, child)
                    if video_node:
                        return video_node
            elif node["kind"] == "Video" and node["slug"] == video_slug:
                return node

            return None

        if node["kind"] == "Exercise":
            videos_to_delete = []
            for vi, video_slug in enumerate(node["related_video_slugs"]):
                if not get_video_node(video_slug, topic_tree):
                    videos_to_delete.append(vi)
            for vi in reversed(videos_to_delete):
                logging.warn("Deleting unknown video %s" % node["related_video_slugs"][vi])
                del node["related_video_slugs"][vi]
        for child in node.get("children", []):
            recurse_nodes_to_clean_related_videos(child)
    recurse_nodes_to_clean_related_videos(topic_tree)


    # Limit exercises to only the previous list
    def recurse_nodes_to_delete_exercise(node):
        """
        Internal function for recursing the topic tree and removing new exercises.
        Requires rebranding of metadata done by recurse_nodes function.
        Returns a list of exercise slugs for the exercises that were deleted.
        """
        # Stop recursing when we hit leaves
        if node["kind"] != "Topic":
            return []

        slugs_deleted = []

        children_to_delete = []
        for ci, child in enumerate(node.get("children", [])):
            # Mark all unrecognized exercises for deletion
            if child["kind"] == "Exercise":
                if not os.path.exists(EXERCISE_FILEPATH_TEMPLATE % child["slug"]):
                    children_to_delete.append(ci)

            # Recurse over children to delete
            elif child.get("children", None):
                slugs_deleted += recurse_nodes_to_delete_exercise(child)

                if not child.get("children", None):
                    # Delete children without children (all their children were removed)
                    logging.warn("Removing now-childless topic node '%s'" % child["slug"])
                    children_to_delete.append(ci)
                elif not any([ch["kind"] == "Exercise" or "Exercise" in ch.get("contains", []) for ch in child["children"]]):
                    # If there are no longer exercises, be honest about it
                    child["contains"] = list(set(child["contains"]) - set(["Exercise"]))

        # Do the actual deletion
        for i in reversed(children_to_delete):
            logging.warn("Deleting unknown exercise %s" % node["children"][i]["slug"])
            del node["children"][i]

        return slugs_deleted

    if remove_unknown_exercises:
        slugs_deleted = recurse_nodes_to_delete_exercise(topic_tree) # do this before [add related]
        for vid, ex in related_exercise.items():
            if ex and ex["slug"] in slugs_deleted:
                related_exercise[vid] = None


    def recurse_nodes_to_add_related_exercise(node):
        """
        Internal function for recursing the topic tree and marking related exercises.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        if node["kind"] == "Video":
            node["related_exercise"] = related_exercise.get(node["slug"], None)
        for child in node.get("children", []):
            recurse_nodes_to_add_related_exercise(child)
    recurse_nodes_to_add_related_exercise(topic_tree)


    def recurse_nodes_to_remove_childless_nodes(node):
        """
        When we remove exercises, we remove dead-end topics.
        Khan just sends us dead-end topics, too.
        Let's remove those too.
        """
        children_to_delete = []
        for ci, child in enumerate(node.get("children", [])):
            # Mark all unrecognized exercises for deletion
            if child["kind"] != "Topic":
                continue

            recurse_nodes_to_remove_childless_nodes(child)

            if not child.get("children"):
                children_to_delete.append(ci)
                logging.warn("Removing KA childless topic: %s" % child["slug"])

        for ci in reversed(children_to_delete):
            del node["children"][ci]
    recurse_nodes_to_remove_childless_nodes(topic_tree)

    return topic_tree


def rebuild_knowledge_map(topic_tree, node_cache, data_path=settings.PROJECT_PATH + "/static/data/", force_icons=False):
    """
    Uses KA Lite topic data and supporting data from Khan Academy
    to rebuild the knowledge map (maplayout.json) and topics.json files.
    """

    knowledge_topics = {}  # Stored variable that keeps all exercises related to second-level topics
                           #   Much of this is duplicate information from node_cache
    #knowledge_map = download_khan_data("http://www.khanacademy.org/api/v1/maplayout")

    def scrub_knowledge_map(knowledge_map, node_cache):
        """
        Some topics in the knowledge map, we don't keep in our topic tree / node cache.
        Eliminate them from the knowledge map here.
        """
        for slug in knowledge_map["topics"].keys():
            nodecache_node = node_cache["Topic"].get(slug, [{}])[0]
            topictree_node = topic_tools.get_topic_by_path(nodecache_node.get("path"), root_node=topic_tree)

            if not nodecache_node or not topictree_node:
                logging.warn("Removing unrecognized knowledge_map topic '%s'" % slug)
            elif not topictree_node.get("children"):
                logging.warn("Removing knowledge_map topic '%s' with no children." % slug)
            elif not "Exercise" in topictree_node.get("contains"):
                logging.warn("Removing knowledge_map topic '%s' with no exercises." % slug)
            else:
                continue

            del knowledge_map["topics"][slug]
            topictree_node["in_knowledge_map"] = False
    #scrub_knowledge_map(knowledge_map, node_cache)


    def recurse_nodes_to_extract_knowledge_map(node, node_cache):
        """
        Internal function for recursing the topic tree and building the knowledge map.
        Requires rebranding of metadata done by recurse_nodes function.
        """
        assert node["kind"] == "Topic"

        if node.get("in_knowledge_map", None):
            if node["slug"] not in knowledge_map["topics"]:
                logging.debug("Not in knowledge map: %s" % node["slug"])
                node["in_knowledge_map"] = False
                for node in node_cache["Topic"][node["slug"]]:
                    node["in_knowledge_map"] = False

            knowledge_topics[node["slug"]] = topic_tools.get_all_leaves(node, leaf_type="Exercise")

            if not knowledge_topics[node["slug"]]:
                sys.stderr.write("Removing topic from topic tree: no exercises. %s" % node["slug"])
                del knowledge_topics[node["slug"]]
                del knowledge_map["topics"][node["slug"]]
                node["in_knowledge_map"] = False
                for node in node_cache["Topic"][node["slug"]]:
                    node["in_knowledge_map"] = False
        else:
            if node["slug"] in knowledge_map["topics"]:
                sys.stderr.write("Removing topic from topic tree; does not belong. '%s'" % node["slug"])
                logging.warn("Removing from knowledge map: %s" % node["slug"])
                del knowledge_map["topics"][node["slug"]]

        for child in [n for n in node.get("children", []) if n["kind"] == "Topic"]:
            recurse_nodes_to_extract_knowledge_map(child, node_cache)
    recurse_nodes_to_extract_knowledge_map(topic_tree, node_cache)


    # Download icons
    def download_kmap_icons(knowledge_map):
        for key, value in knowledge_map["topics"].items():
            # Note: id here is retrieved from knowledge_map, so we're OK
            #   that we blew away ID in the topic tree earlier.
            if "icon_url" not in value:
                logging.warn("No icon URL for %s" % key)

            value["icon_url"] = iconfilepath + value["id"] + iconextension
            knowledge_map["topics"][key] = value

            out_path = data_path + "../" + value["icon_url"]
            if os.path.exists(out_path) and not force_icons:
                continue

            icon_khan_url = "http://www.khanacademy.org" + value["icon_url"]
            sys.stdout.write("Downloading icon %s from %s..." % (value["id"], icon_khan_url))
            sys.stdout.flush()
            try:
                icon = requests.get(icon_khan_url)
            except Exception as e:
                sys.stdout.write("\n")  # complete the "downloading" output
                sys.stderr.write("Failed to download %-80s: %s\n" % (icon_khan_url, e))
                continue
            if icon.status_code == 200:
                iconfile = file(data_path + "../" + value["icon_url"], "w")
                iconfile.write(icon.content)
            else:
                sys.stdout.write(" [NOT FOUND]")
                value["icon_url"] = iconfilepath + defaulticon + iconextension
            sys.stdout.write(" done.\n")  # complete the "downloading" output
    download_kmap_icons(knowledge_map)


    # Clean the knowledge map
    def clean_orphaned_polylines(knowledge_map):
        """
        We remove some topics (without leaves); need to remove polylines associated with these topics.
        """
        all_topic_points = [(km["x"],km["y"]) for km in knowledge_map["topics"].values()]

        polylines_to_delete = []
        for li, polyline in enumerate(knowledge_map["polylines"]):
            if any(["x" for pt in polyline["path"] if (pt["x"], pt["y"]) not in all_topic_points]):
                polylines_to_delete.append(li)

        logging.warn("Removing %s of %s polylines in top-level knowledge map" % (len(polylines_to_delete), len(knowledge_map["polylines"])))
        for i in reversed(polylines_to_delete):
            del knowledge_map["polylines"][i]

        return knowledge_map
    clean_orphaned_polylines(knowledge_map)


    def normalize_tree(knowledge_map, knowledge_topics):
        """
        The knowledge map is currently arbitrary coordinates, with a lot of space
        between nodes.

        The code below adjusts the space between nodes.  Our code
        in kmap-editor.js adjust coordinates based on screen size.

        TODO(bcipolli): normalize coordinates to range [0,1]
        that will make code for expanding out to arbitrary screen
        sizes much more simple.
        """

        def adjust_coord(children, prop_name):

            allX = [ch[prop_name] for ch in children]
            minX = min(allX)
            maxX = max(allX)
            rangeX = maxX - minX + 1
            if not rangeX:
                return children

            filledX = [False] * rangeX

            # Mark all the places where an object is found
            for ch in children:
                filledX[ch[prop_name] - minX] = True

            # calculate how much each row/column need to be shifted to fill in the gaps,
            #   by seeing how many positions along the way are gaps,
            #   then trying to minimize them
            shiftX = [0] * rangeX
            shift = 0
            for ii in range(rangeX):
                if not filledX[ii]:
                    shift -= 1   # move increasingly left, to close gaps
                shiftX[ii] = shift

            # shift each exercise to fill in the gaps
            for ch in children:
                ch[prop_name] += shiftX[ch[prop_name] - minX]

            return children

        # mark the children as not yet having been flipped, so we can avoid flipping twice later
        for children in knowledge_topics.itervalues():
            for ch in children:
                ch["unflipped"] = True

        # NOTE that we are not adjusting any coordinates in
        #   the knowledge map, or in the polylines.
        for slug, children in knowledge_topics.iteritems():
            # Flip coordinates, but only once per node
            for ch in children:
                if ch.get("unflipped", False):
                    ch["v_position"], ch["h_position"] = ch["h_position"], ch["v_position"]
                    del ch["unflipped"]

            # Adjust coordinates
            adjust_coord(children, "v_position")  # side-effect directly into 'children'
            adjust_coord(children, "h_position")

        return knowledge_map, knowledge_topics
    normalize_tree(knowledge_map, knowledge_topics)

    def stamp_knowledge_map_on_topic_tree(node_cache, knowledge_map, knowledge_topics):
        """
        Any topic node can have a "knowledge map" property.
        If it does, it can have two components:
        1. nodes: a dictionary containing node ids and a few values, including:
            - kind (the kind of node)
            - h_position / v_position
            - optional "icon_url"
        2. polylines (optional)
          - defines the connections between nodes

        So now, when you have a topic node, it contains in itself
          enough data to pull together a knowledge map on the fly.
        """
        # Move over the root map
        root_map = {}
        for topic in knowledge_map["topics"].values():
            root_map[topic["id"]] = {
                "kind": "Topic",
                "h_position": topic["x"],
                "v_position": topic["y"],
                "icon_url": topic["icon_url"],
            }
        root_node = node_cache["Topic"]["root"][0]
        root_node["knowledge_map"] = {
            "nodes": root_map,
            "polylines": knowledge_map["polylines"],
        }

        # Move over subtopic paths
        for topic_id, subtopic_data in knowledge_topics.iteritems():
            # Move over the root map
            topic_map = {}
            for subtopic in subtopic_data:
                topic_map[subtopic["id"]] = {
                    "kind": "Exercise",
                    "h_position": subtopic["h_position"],
                    "v_position": subtopic["v_position"],
                }
            for node in node_cache["Topic"][topic_id]:
                node["icon_url"] = node["icon_src"]
                node["knowledge_map"] = {
                    "nodes": topic_map,
                }
    stamp_knowledge_map_on_topic_tree(node_cache, knowledge_map, knowledge_topics)

    return knowledge_map, knowledge_topics


def validate_data(topic_tree, node_cache, slug2id_map):

    # Validate related videos
    for exercise_nodes in node_cache['Exercise'].values():
        exercise = exercise_nodes[0]
        exercise_path = EXERCISE_FILEPATH_TEMPLATE % exercise["slug"]
        if not os.path.exists(exercise_path):
            sys.stderr.write("Could not find exercise HTML file: %s\n" % exercise_path)
        for vid_slug in exercise.get("related_video_slugs", []):
            if vid_slug not in slug2id_map or slug2id_map[vid_slug] not in node_cache["Video"]:
                sys.stderr.write("Could not find related video %s in node_cache (from exercise %s)\n" % (vid_slug, exercise["slug"]))

    # Validate related exercises
    for video_nodes in node_cache["Video"].values():
        video = video_nodes[0]
        ex = video["related_exercise"]
        if ex and ex["slug"] not in node_cache["Exercise"]:
            sys.stderr.write("Could not find related exercise %s in node_cache (from video %s)\n" % (ex["slug"], video["slug"]))

    # Validate all topics have leaves
    for topic_nodes in node_cache["Topic"].values():
        topic = topic_nodes[0]
        if not topic_tools.get_topic_by_path(topic["path"], root_node=topic_tree).get("children"):
            sys.stderr.write("Could not find any children for topic %s\n" % (topic["path"]))


def scrub_topic_tree(node_cache):
    # Now, remove unnecessary values
    for kind_nodes in node_cache.values():
        for node_list in kind_nodes.values():
            for node in node_list:
                for att in temp_ok_atts:
                    if att in node:
                        if att == "hide"and node["id"] != "root":
                            assert node[att] == False, "All hidden nodes (%s) better be deleted by this point!" % node["id"]
                        if att == "live":
                            assert node[att] == True, "All non-live nodes (%s) better be deleted by this point!" % node["id"]
                        del node[att]


def save_topic_tree(topic_tree=None, node_cache=None, data_path=os.path.join(settings.PROJECT_PATH, "static", "data")):
    assert bool(topic_tree) + bool(node_cache) == 1, "Must specify either topic_tree or node_cache parameter"

    # Dump the topic tree (again)
    topic_tree = topic_tree or node_cache["Topic"]["root"][0]

    dest_filepath = os.path.join(data_path, topic_tools.TOPICS_FILEPATH)
    logging.debug("Saving topic tree to %s" % dest_filepath)
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(topic_tree, indent=2))



class Command(BaseCommand):
    help = """**WARNING** not intended for use outside of the FLE; use at your own risk!
    Update the topic tree caches from Khan Academy.
    Options:
        [no args] - download from Khan Academy and refresh all files
    """

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-i', '--force-icons',
            action='store_true',
            dest='force_icons',
            default=False,
            help='Force the download of each icon'),
        make_option('-k', '--keep-new-exercises',
            action='store_true',
            dest='keep_new_exercises',
            default=False,
            help="Keep data on new exercises (if not specified, these are stripped out, as we don't have code to download/use them)"),
    )

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Unknown argument list: %s" % args)

        # TODO(bcipolli)
        # Make remove_unknown_exercises and force_icons into command-line arguments
        topic_tree = rebuild_topictree(remove_unknown_exercises=not options["keep_new_exercises"])
        node_cache = topic_tools.generate_node_cache(topic_tree)
        slug2id_map = topic_tools.generate_slug_to_video_id_map(node_cache)

        # Disabled until we revamp it based on the current KA API.
        # h_position and v_position are available on each exercise now.
        # If not on the topic_tree, then here: http://api-explorer.khanacademy.org/api/v1/playlists/topic_slug/exercises
        rebuild_knowledge_map(topic_tree, node_cache, force_icons=options["force_icons"])

        scrub_topic_tree(node_cache=node_cache)

        validate_data(topic_tree, node_cache, slug2id_map)

        save_topic_tree(topic_tree)

        sys.stdout.write("Downloaded topic_tree data for %d topics, %d videos, %d exercises\n" % (
            len(node_cache["Topic"]),
            len(node_cache["Video"]),
            len(node_cache["Exercise"]),
        ))
