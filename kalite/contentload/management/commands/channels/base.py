"""
Base module for building the topic tree, used in the sidebar among other places.
Don't import this! Instead import one of the other modules in this directory depending on the source of your content.
Modules need to define:
    path:

    channel_data_path:

    rebuild_topictree: see docstring below

    build_full_cache:

    channel_data:

    channel_data_files:

    retrieve_API_data: see docstring below

"""
import copy

from math import ceil, log, exp  # needed for basepoints calculation

from django.conf import settings; logging = settings.LOG

from django.utils.text import slugify

# A module-level channel_data dict needs to be defined.
# For specification of channel_data dictionary, please see CHANNELDATA.md

def retrieve_API_data():
    """
    A function that returns the topic tree and associated data for content items. Should be defined by each
        channel-specific submodule. This particular function returns a totally empty topic tree.

    :return: A tuple, `(topic_tree, exercises, assessment_items, content)`.
        topic_tree: A dictionary. Tree-like structure of topics & subtopics, where leaves are content items.
                    Should only represent hierarchical relationships, with full node data in the lists below.
        exercises, assessment_items, content: lists. A list of nodes for each content type.
    """

    topic_tree = {}

    exercises = []

    assessment_items = []

    content = []

    return topic_tree, exercises, assessment_items, content


def whitewash_node_data(node, path="", channel_data={}):
    """
    Utility function to convert nodes into the format used by KA Lite.
    Extracted from other functions so as to be reused by both the denormed
    and fully inflated exercise and video nodes.

    :param node: A dictionary. The input node with potentially extra keys.
    :param path: ????
    :param channel_data: A channel_data dict as described in CHANNELDATA.md
    :return: node, with extra keys stripped out.
    """

    kind = node.get("kind", None)

    if not kind:
        return node

    # Only keep key data we can use
    if kind in channel_data["attribute_whitelists"]:
        for key in node.keys():
            if (key not in channel_data["attribute_whitelists"][kind] and key not in channel_data["temp_ok_atts"]):
                del node[key]

    node["id"] = node.get(channel_data["id_key"].get(kind, ""), node.get("id", ""))

    # Fix up data
    if channel_data["slug_key"][kind] not in node:
        node[channel_data["slug_key"][kind]] = node["id"]

    node["slug"] = node[channel_data["slug_key"][kind]] if node[channel_data["slug_key"][kind]] != "root" else "khan"
    node["slug"] = slugify(unicode(node["slug"]))

    node["path"] = node.get("path", "") or path + node["slug"] + "/"
    if "title" not in node:
        node["title"] = (node.get(channel_data["title_key"][kind], ""))
    node["title"] = (node["title"] or "").strip()

    if "description" in node:
        node["description"] = node["description"].strip()

    if kind == "Video":
        # TODO: map new videos into old videos; for now, this will do nothing.
        node["video_id"] = node.get("youtube_id", "")

    elif kind == "Exercise":
        # For each exercise, need to set the exercise_id
        #   get related videos
        #   and compute base points
        node["exercise_id"] = node["id"]

        # compute base points
        # Minimum points per exercise: 5
        node["basepoints"] = ceil(7 * log(max(exp(5. / 7), node.get("seconds_per_fast_problem", 0))))

    return node


def rebuild_topictree(
        whitewash_node_data=whitewash_node_data,
        retrieve_API_data=retrieve_API_data,
        channel_data={},
        channel=None):
    """
    Downloads topictree (and supporting) data and uses it to rebuild the KA Lite topictree cache (topics.json).
    Does this by collecting all relevant topic_tree and content data from data source.
    Recurses over the entire topic tree to remove extraneous data.
    Denorms content data to reduce the bulk of the topic tree.
    Adds position data to every node in the topic tree.

    :param whitewash_node_data: A function. See docstring above. Strips topic tree nodes of extraneous keys.
    :param retrieve_API_data: A function. See docstring above. Defines the return type of rebuild_topictree.
    :param channel_data: A channel_data dict as described in CHANNELDATA.md
    :param channel: keyword arg passed in to retrieve_API_data

    :return: A tuple `(topic_tree, exercises, assessment_items, contents)`.
        The items in this tuple are defined by retrieve_API_data.
    """
    
    topic_tree, exercises, assessment_items, contents = retrieve_API_data(channel=channel)

    exercise_lookup = dict((exercise["id"], exercise) for exercise in exercises)

    content_lookup = dict((content["id"], content) for content in contents)

    def recurse_nodes(node, path=""):
        """
        Internal function for recursing over the topic tree, marking relevant metadata,
        and removing undesired attributes and children.
        """

        kind = node["kind"]

        node = whitewash_node_data(node, path)

        if kind != "Topic":
            if kind in channel_data["denormed_attribute_list"]:
                for key in node.keys():
                    if key not in channel_data["denormed_attribute_list"][kind] or not node.get(key, ""):
                        del node[key]

        if "child_data" in node:
            # Loop through children, remove exercises and videos to reintroduce denormed data
            # Only do this for data that has child_data (at the moment Khan Academy)
            # Otherwise, repositories that have all their data directly in the topic tree
            # Will lose their data - e.g. Videos from the channel_import tool.
            children_to_delete = []
            child_kinds = set()
            for i, child in enumerate(node.get("children", [])):
                child_kind = child.get("kind", None)

                if child_kind == "Video" or child_kind == "Exercise":
                    children_to_delete.append(i)

            for i in reversed(children_to_delete):
                # Reversing means that earlier indices are unaffected by deletion of later ones.
                del node["children"][i]

        # Loop through child_data to populate children with denormed data of exercises and videos.
        for child_datum in node.get("child_data", []):
            try:
                child_id = str(child_datum["id"])
                child_kind = child_datum["kind"]
                slug_key = channel_data["slug_key"][child_kind]
                if child_kind == "Exercise":
                    child_denormed_data = exercise_lookup[child_id]
                    # Add path information here
                    slug = exercise_lookup[child_id][slug_key] if exercise_lookup[child_id][slug_key] != "root" else "khan"
                    slug = slugify(unicode(slug))
                    exercise_lookup[child_id]["path"] = node["path"] + slug + "/"
                elif child_kind == "Video":
                    child_denormed_data = content_lookup[child_id]
                    # Add path information here
                    slug = content_lookup[child_id][slug_key] if content_lookup[child_id][slug_key] != "root" else "khan"
                    slug = slugify(unicode(slug))
                    content_lookup[child_id]["path"] = node["path"] + slug + "/"
                else:
                    child_denormed_data = None
                if child_denormed_data:
                    node["children"].append(copy.deepcopy(dict(child_denormed_data)))
            except KeyError:
                logging.warn("%(kind)s %(id)s does not exist in lookup table" % child_datum)

        # Recurse through children, remove any blacklisted items
        children_to_delete = []
        child_kinds = set()
        for i, child in enumerate(node.get("children", [])):
            child_kind = child.get("kind", None)

            # Blacklisted--remove
            if child_kind in channel_data["kind_blacklist"]:
                children_to_delete.append(i)
                continue
            elif child[channel_data["slug_key"][child_kind]] in channel_data["slug_blacklist"]:
                children_to_delete.append(i)
                continue
            elif not child.get("live", True):  # node is not live
                logging.debug("Removing non-live child: %s" % child[channel_data["slug_key"][child_kind]])
                children_to_delete.append(i)
                continue
            elif child.get("hide", False):  # node is hidden. Note that root is hidden, and we're implicitly skipping that.
                children_to_delete.append(i)
                logging.debug("Removing hidden child: %s" % child[channel_data["slug_key"][child_kind]])
                continue
            elif child_kind == "Video" and set(["mp4", "png"]) - set(child.get("download_urls", {}).keys()):
                # for now, since we expect the missing videos to be filled in soon,
                #   we won't remove these nodes
                logging.warn("No download link for video: %s\n" % child.get("youtube_id", child.get("id", "")))
                if channel_data.get("require_download_link", False):
                    children_to_delete.append(i)
                continue

            child_kinds = child_kinds.union(set([child_kind]))
            child_kinds = child_kinds.union(recurse_nodes(child, path=node["path"]))

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
        Remove dead-end topics.
        """
        children_to_delete = []
        for ci, child in enumerate(node.get("children", [])):
            if child["kind"] != "Topic":
                continue

            recurse_nodes_to_remove_childless_nodes(child)

            if not child.get("children"):
                children_to_delete.append(ci)
                logging.warn("Removing childless topic: %s" % child["slug"])

        for ci in reversed(children_to_delete):
            del node["children"][ci]
    recurse_nodes_to_remove_childless_nodes(topic_tree)

    return topic_tree, exercises, assessment_items, contents


def recurse_topic_tree_to_create_hierarchy(node, level_cache={}, hierarchy=[]):
    if not level_cache:
        for hier in hierarchy:
            level_cache[hier] = []
    render_type = node.get("render_type", "")
    if render_type in hierarchy:
        node_copy = copy.deepcopy(dict(node))
        for child in node_copy.get("children", []):
            if "children" in child:
                del child["children"]
        level_cache[render_type].append(node_copy)
    for child in node.get("children", []):
        recurse_topic_tree_to_create_hierarchy(child, level_cache, hierarchy=hierarchy)
    return level_cache
