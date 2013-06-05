import json, requests, copy, os

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites"]
}

slug_key = {
    "Topic": "id",
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

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res"]

def download_topictree():
    
    topics = json.loads(requests.get("http://www.khanacademy.org/api/v1/topictree").content)

    node_cache = {}
    
    related_exercise = {}

    def recurse_nodes(node, path=""):

        kind = node["kind"]
        
        keys_to_delete = []
        
        for key in node:
            if key not in attribute_whitelists[kind]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del node[key]

        node["slug"] = node[slug_key[kind]]
        if node["slug"]=="root":
            node["slug"] = ""
        node["title"] = node[title_key[kind]]
        node["path"] = path + kind_slugs[kind] + node["slug"] + "/"
        
        node_cache[kind] = node_cache.get(kind, {})
        node_copy = copy.copy(node)
        if "children" in node_copy:
            del node_copy["children"]
        node_cache[kind][node["slug"]] = node_copy

        kinds = set([kind])

        if kind == "Exercise":
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
        
        if kind=="Topic":
            node["contains"] = list(kinds)
        
        return kinds

    def recurse_nodes_to_add_related_exercise(node):
        if node["kind"] == "Video":
            node["related_exercise"] = related_exercise.get(node["slug"], None)
        for child in node.get("children", []):
            recurse_nodes_to_add_related_exercise(child)
            
    recurse_nodes(topics)
    recurse_nodes_to_add_related_exercise(topics)
    
    with open(data_path + "topics.json", "w") as fp:
        fp.write(json.dumps(topics, indent=2))
    
    with open(data_path + "nodecache.json", "w") as fp:
        fp.write(json.dumps(node_cache, indent=2))



def scrub_topics(topic_node):
    """Seems that topics.json has cruft in it.  Scrub it!"""
    global kind_blacklist
    
    if topic_node["kind"] in kind_blacklist:
#        if topic_node["kind"] == "Separator":
#            print topic_node
#        else:
#            import pdb; pdb.set_trace()
        return None
    elif topic_node["slug"] in slug_blacklist:
        return None
        
    for ci,child in enumerate(topic_node.get("children", [])):
        if not scrub_topics(child):
            topic_node['children'].pop(ci)

    return topic_node  
    
    
def node_cache_from_topic(topic_node, node_cache={}):
    """Get the node_cache from the topics list (saves disk space!)"""
    
    kind = topic_node["kind"]
    
    node_cache[kind] = node_cache.get(kind, {})
    node_copy = copy.copy(topic_node)
    if "children" in node_copy:
        del node_copy["children"]
    node_cache[kind][node_copy["slug"]] = node_copy

    for child in topic_node.get("children", []):
        node_cache_from_topic(child, node_cache)

    return node_cache