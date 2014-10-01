from khan_api_python.api_models import Khan, APIError
from functools import partial
import base

slug_key = {
    "Topic": "name",
    "Video": "name",
    "Exercise": "name",
    "AssessmentItem": "name",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "title",
    "AssessmentItem": "title"
}

id_key = {
    "Topic": "id",
    "Video": "id",
    "Exercise": "id",
    "AssessmentItem": "id"
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src", "child_data", "render_type", "path", "slug"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id", "y_pos", "x_pos", "in_knowledge_map", "path", "slug"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "y_pos", "x_pos", "in_knowledge_map", "all_assessment_items", "uses_assessment_items", "path", "slug"],
    "AssessmentItem": ["kind", "name", "item_data", "tags", "author_names", "sha", "id"]
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "duration", "youtube_id", "readable_id", "id", "y_pos", "x_pos", "path", "slug"],
    "Exercise": ["kind", "description", "title", "display_name", "name", "id", "y_pos", "x_pos", "path", "slug"]
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
   " iconextension":  iconextension,
    "defaulticon": defaulticon,
    "attribute_whitelists": attribute_whitelists,
    "denormed_attribute_list": denormed_attribute_list,
    "kind_blacklist": kind_blacklist,
    "slug_blacklist": slug_blacklist,
    "temp_ok_atts": temp_ok_atts,
}

whitewash_node_data = partial(base.whitewash_node_data, channel_data=channel_data)

def build_full_cache(items, id_key="id"):
    """
    Uses list of items retrieved from Khan Academy API to
    create an item cache with fleshed out meta-data.
    """
    return {item["id"]: whitewash_node_data(item) for item in items}

hierarchy = ["Domain", "Subject", "Topic", "Tutorial"]

path = ""

def retrieve_API_data():

    topic_tree = {}

    exercises = []

    videos = []

    assessment_items = []

    content = []

    return topic_tree, exercises, videos, assessment_items, content

recurse_topic_tree_to_create_hierarchy = partial(base.recurse_topic_tree_to_create_hierarchy, hierarchy=hierarchy)

rebuild_topictree = partial(base.rebuild_topictree, whitewash_node_data=whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=channel_data)