import json
import requests
import copy
import os

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

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


def download_topictree():

    topics = json.loads(requests.get("http://www.khanacademy.org/api/v1/topictree").content)

    node_cache = {}

    knowledge_topics = {}

    knowledge_map = json.loads(requests.get("http://www.khanacademy.org/api/v1/maplayout").content)

    related_exercise = {}

    def recurse_nodes(node, path=""):

        kind = node["kind"]

        keys_to_delete = []

        for key in node:
            if key not in attribute_whitelists[kind]:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del node[key]

        try:
            node["slug"] = node[slug_key[kind]]
            if node["slug"] == "root":
                node["slug"] = ""
        except KeyError:
            print node.keys()
        node["title"] = node[title_key[kind]]
        node["path"] = path + kind_slugs[kind] + node["slug"] + "/"

        node_cache[kind] = node_cache.get(kind, {})
        node_copy = copy.copy(node)
        if "children" in node_copy:
            del node_copy["children"]
        node_cache[kind][node["slug"]] = node_copy

        kinds = set([kind])

        if kind == "Exercise":
            related_video_readable_ids = [vid["readable_id"] for vid in json.loads(requests.get("http://www.khanacademy.org/api/v1/exercises/%s/videos" % node["name"]).content)]
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

    for key, value in knowledge_map["topics"].items():
        if "icon_url" in value:
            value["icon_url"] = iconfilepath + value["id"] + iconextension
            knowledge_map["topics"][key] = value
            icon = requests.get("http://www.khanacademy.org" + value["icon_url"])
            if icon.status_code == 200:
                iconfile = file(data_path + "../" + value["icon_url"], "w")
                iconfile.write(icon.content)
            else:
                value["icon_url"] = iconfilepath + defaulticon + iconextension

    recurse_nodes(topics)
    recurse_nodes_to_add_related_exercise(topics)
    recurse_nodes_to_extract_knowledge_map(topics)

    with open(data_path + "topics.json", "w") as fp:
        fp.write(json.dumps(topics, indent=2))

    with open(data_path + "nodecache.json", "w") as fp:
        fp.write(json.dumps(node_cache, indent=2))

    with open(data_path + "maplayout_data.json", "w") as fp:
        fp.write(json.dumps(knowledge_map, indent=2))

    for key, value in knowledge_topics.items():
        with open(data_path + "topicdata/%s.json" % key, "w") as fp:
            fp.write(json.dumps(value, indent=2))
