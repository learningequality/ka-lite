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

from khan_api_python.api_models import Khan
from math import ceil, log, exp  # needed for basepoints calculation
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError

from ... import KHANLOAD_CACHE_DIR, kind_slugs
from fle_utils.general import datediff
from kalite import topic_tools


# get the path to an exercise file, so we can check, below, which ones exist
EXERCISE_FILEPATH_TEMPLATE = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", "%s.html")

slug_key = {
    "Topic": "node_slug",
    "Video": "readable_id",
    "Exercise": "name",
    "AssessmentItem": "id",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
    "AssessmentItem": "name"
}

id_key = {
    "Topic": "node_slug",
    "Video": "youtube_id",
    "Exercise": "name",
    "AssessmentItem": "id"
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src", "child_data"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "v_position", "h_position", "all_assessment_items", "uses_assessment_items"],
    "AssessmentItem": ["kind", "name", "item_data", "tags", "author_names", "sha", "id"]
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "duration", "youtube_id", "readable_id"],
    "Exercise": ["kind", "description", "display_name", "name"]
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


def whitewash_node_data(node, path="", ancestor_ids=[]):
    """
    Utility function to convert nodes into the format used by KA Lite.
    Extracted from other functions so as to be reused by both the denormed
    and fully inflated exercise and video nodes.
    """

    kind = node["kind"]

    # Only keep key data we can use
    for key in node.keys():
        if key not in attribute_whitelists[kind]:
            del node[key]

    # Fix up data
    if slug_key[kind] not in node:
        # logging.warn("Could not find expected slug key (%s) on node: %s" % (slug_key[kind], node))
        node[slug_key[kind]] = node["id"]  # put it SOMEWHERE.
    node["slug"] = node[slug_key[kind]] if node[slug_key[kind]] != "root" else ""
    node["id"] = node[id_key[kind]]  # these used to be the same; now not. Easier if they stay the same (issue #233)

    node["path"] = path + kind_slugs[kind] + node["slug"] + "/"
    node["title"] = node[title_key[kind]].strip()

    # Add some attribute that should have been on there to start with.
    node["parent_id"] = ancestor_ids[-1] if ancestor_ids else None
    node["ancestor_ids"] = ancestor_ids

    if kind == "Video":
        # TODO: map new videos into old videos; for now, this will do nothing.
        node["video_id"] = node["youtube_id"]

    elif kind == "Exercise":
        # For each exercise, need to set the exercise_id
        #   get related videos
        #   and compute base points
        node["exercise_id"] = node["slug"]

        # compute base points
        # Minimum points per exercise: 5
        # node["basepoints"] = ceil(7 * log(max(exp(5./7), node.get("seconds_per_fast_problem", 0))));

    return node

def rebuild_topictree(remove_unknown_exercises=False, remove_disabled_topics=True):
    """Downloads topictree (and supporting) data from Khan Academy and uses it to
    rebuild the KA Lite topictree cache (topics.json).
    """

    khan = Khan()

    topic_tree = khan.get_topic_tree()

    exercises = khan.get_exercises()

    exercise_lookup = {exercise["id"]: exercise for exercise in exercises}

    videos = khan.get_videos()

    video_lookup = {video["id"]: video for video in videos}

    assessment_items = []

    for exercise in exercises:
        for assessment_item in exercise.all_assessment_items:
            assessment_items.append(khan.get_assessment_item(assessment_item["id"]))

    #Do Something Terrible Today

    def recurse_nodes(node, path="", ancestor_ids=[]):
        """
        Internal function for recursing over the topic tree, marking relevant metadata,
        and removing undesired attributes and children.
        """

        kind = node["kind"]

        node = whitewash_node_data(node, path, ancestor_ids)

        if kind == "Exercise" or kind == "Video":
            for key in node.keys():
                if key not in denormed_attribute_list[kind]:
                    del node[key]

        # Loop through children, remove exercises and videos to reintroduce denormed data
        children_to_delete = []
        child_kinds = set()
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)

            if child_kind=="Video" or child_kind=="Exercise":
                children_to_delete.append(i)

        for i in reversed(children_to_delete):
            # Reversing means that earlier indices are unaffected by deletion of later ones.
            del node["children"][i]

        # Loop through child_data to populate children with denormed data of exercises and videos.
        for child_datum in node.get("child_data", []):
            try:
                if child_datum["kind"] == "Exercise":
                    child_denormed_data = exercise_lookup[str(child_datum["id"])]
                elif child_datum["kind"] == "Video":
                    child_denormed_data = video_lookup[str(child_datum["id"])]
                else:
                    child_denormed_data = None
                if child_denormed_data:
                    node["children"].append(copy.deepcopy(child_denormed_data))
            except KeyError as e:
                logging.warn("%(kind)s %(id)s does not exist in lookup table" % child_datum)


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
                logging.debug("Removing non-live child: %s" % child[slug_key[child_kind]])
                children_to_delete.append(i)
                continue
            elif child.get("hide", False) and remove_disabled_topics:  # node is hidden. Note that root is hidden, and we're implicitly skipping that.
                children_to_delete.append(i)
                logging.debug("Removing hidden child: %s" % child[slug_key[child_kind]])
                continue
            elif child_kind == "Video" and set(["mp4", "png"]) - set(child.get("download_urls", {}).keys()):
                # for now, since we expect the missing videos to be filled in soon,
                #   we won't remove these nodes
                sys.stderr.write("WARNING: No download link for video: %s\n" % child["youtube_id"])
                children_to_delete.append(i)
                continue

            child_kinds = child_kinds.union(set([child_kind]))
            child_kinds = child_kinds.union(recurse_nodes(child, path=node["path"], ancestor_ids=ancestor_ids + [node["id"]]))

        # Delete those marked for completion
        for i in reversed(children_to_delete):
            # Reversing means that earlier indices are unaffected by deletion of later ones.
            del node["children"][i]

        # Mark on topics whether they contain Videos, Exercises, or both
        if kind == "Topic":
            node["contains"] = list(child_kinds)

        return child_kinds
    recurse_nodes(topic_tree)

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

    return topic_tree, exercises, videos, assessment_items

def build_full_cache(items, id_key="id"):
    """
    Uses list of items retrieved from Khan Academy API to
    create an item cache with fleshed out meta-data.
    """
    for item in items:
        for attribute in item._API_attributes:
            dummy_variable_to_force_fetch = item.__getattr__(attribute)
    return {item["id"]: whitewash_node_data(item) for item in items}


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
    for exercise in node_cache['Exercise'].values():
        exercise_path = EXERCISE_FILEPATH_TEMPLATE % exercise["slug"]
        if not os.path.exists(exercise_path):
            sys.stderr.write("Could not find exercise HTML file: %s\n" % exercise_path)
        for vid_slug in exercise.get("related_video_slugs", []):
            if vid_slug not in slug2id_map or slug2id_map[vid_slug] not in node_cache["Video"]:
                sys.stderr.write("Could not find related video %s in node_cache (from exercise %s)\n" % (vid_slug, exercise["slug"]))

    # Validate related exercises
    for video in node_cache["Video"].values():
        ex = video.get("related_exercise", None)
        if ex:
            if ex["slug"] not in node_cache["Exercise"]:
                sys.stderr.write("Could not find related exercise %s in node_cache (from video %s)\n" % (ex["slug"], video["slug"]))

    # Validate all topics have leaves
    for topic in node_cache["Topic"].values():
        if not topic_tools.get_topic_by_path(topic["path"], root_node=topic_tree).get("children"):
            sys.stderr.write("Could not find any children for topic %s\n" % (topic["path"]))

def scrub_topic_tree(node_cache):
    # Now, remove unnecessary values
    for kind_nodes in node_cache.values():
        for node in kind_nodes.values():
            for att in temp_ok_atts:
                if att in node:
                    if att == "hide" and node["id"] != "root":
                        assert node[att] == False, "All hidden nodes (%s) better be deleted by this point!" % node["id"]
                    if att == "live":
                        assert node[att] == True, "All non-live nodes (%s) better be deleted by this point!" % node["id"]
                    del node[att]



def save_topic_tree(topic_tree=None, node_cache=None, data_path=os.path.join(settings.PROJECT_PATH, "static", "data")):
    assert bool(topic_tree) + bool(node_cache) == 1, "Must specify either topic_tree or node_cache parameter"
    # Dump the topic tree (again)
    topic_tree = topic_tree or node_cache["Topic"]["root"]

    dest_filepath = os.path.join(data_path, topic_tools.TOPICS_FILEPATH)
    logging.debug("Saving topic tree to %s" % dest_filepath)
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(dict(topic_tree)))


def save_cache_file(cache_type, cache_object=None, node_cache=None, data_path=settings.KHAN_DATA_PATH):
    
    cache_object = cache_object or node_cache[cache_object]

    dest_filepath = os.path.join(data_path, cache_type.lower() + "s.json")
    logging.debug("Saving %(cache_type)s to %(dest_filepath)s" % {"cache_type": cache_type, "dest_filepath": dest_filepath})
    with open(dest_filepath, "w") as fp:
        fp.write(json.dumps(cache_object))


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
        topic_tree, exercises, videos, assessment_items = rebuild_topictree()

        exercise_cache = build_full_cache(exercises, id_key=id_key["Exercise"])
        video_cache = build_full_cache(videos, id_key=id_key["Video"])
        assessment_item_cache = build_full_cache(assessment_items)
        
        node_cache = topic_tools.generate_node_cache(topic_tree)
        
        node_cache["Exercise"] = exercise_cache
        node_cache["Video"] = video_cache
        slug2id_map = topic_tools.generate_slug_to_video_id_map(node_cache)
        
        # Disabled until we revamp it based on the current KA API.
        # h_position and v_position are available on each exercise now.
        # If not on the topic_tree, then here: http://api-explorer.khanacademy.org/api/v1/playlists/topic_slug/exercises
        # rebuild_knowledge_map(topic_tree, node_cache, force_icons=options["force_icons"])

        scrub_topic_tree(node_cache=node_cache)

        validate_data(topic_tree, node_cache, slug2id_map)

        save_topic_tree(topic_tree)
        save_cache_file("Exercise", cache_object=exercise_cache)
        save_cache_file("Video", cache_object=video_cache)
        save_cache_file("AssessmentItem", cache_object=assessment_item_cache)

        sys.stdout.write("Downloaded topic_tree data for %d topics, %d videos, %d exercises\n" % (
            len(node_cache["Topic"]),
            len(node_cache["Video"]),
            len(node_cache["Exercise"]),
        ))
