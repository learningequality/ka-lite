from khan_api_python.api_models import Khan, APIError
from functools import partial
import base

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
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src", "child_data", "render_type", "path", "slug"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id", "y_pos", "x_pos", "in_knowledge_map", "path", "slug"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "y_pos", "x_pos", "in_knowledge_map", "all_assessment_items", "uses_assessment_items", "path", "slug"],
    "AssessmentItem": ["kind", "name", "item_data", "tags", "author_names", "sha", "id"]
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "id", "slug"],
    "Exercise": ["kind", "description", "title", "id", "slug"]
}

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res", "MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "cs", "cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math", "cc-seventh-grade-math", "cc-eighth-grade-math", "hour-of-code"]

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = ["x_pos", "y_pos", "icon_src", u'topic_page_url', u'hide', "live", "node_slug", "extended_slug"]

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

def denorm_data(node):
    if node:
        kind = node.get("kind", "")
        if channel_data["denormed_attribute_list"].has_key(kind):
            for key in node.keys():
                if key not in channel_data["denormed_attribute_list"][kind] or not node.get(key, ""):
                    del node[key]


def build_full_cache(items, id_key="id"):
    """
    Uses list of items retrieved from Khan Academy API to
    create an item cache with fleshed out meta-data.
    """
    for item in items:
        for attribute in item._API_attributes:
            try:
                dummy_variable_to_force_fetch = item.__getattr__(attribute)
                if isinstance(item[attribute], list):
                    for subitem in item[attribute]:
                        if isinstance(subitem, dict):
                            if subitem.has_key("kind"):
                                subitem = whitewash_node_data(
                                    {key: value for key, value in subitem.items()})
                                denorm_data(subitem)
                elif isinstance(item[attribute], dict):
                    if item[attribute].has_key("kind"):
                        item[attribute] = whitewash_node_data(
                            {key: value for key, value in item.attribute.items()})
                        denorm_data(item[attribute])
            except APIError as e:
                del item[attribute]
    return {item["id"]: whitewash_node_data(item) for item in items}

hierarchy = ["Domain", "Subject", "Topic", "Tutorial"]

def retrieve_API_data(channel=None):
    khan = Khan()

    topic_tree = khan.get_topic_tree()

    exercises = khan.get_exercises()

    videos = khan.get_videos()

    assessment_items = []

    # for exercise in exercises:
    #     for assessment_item in exercise.all_assessment_items:
    #         assessment_items.append(khan.get_assessment_item(assessment_item["id"]))

    content = []

    return topic_tree, exercises, videos, assessment_items, content

recurse_topic_tree_to_create_hierarchy = partial(base.recurse_topic_tree_to_create_hierarchy, hierarchy=hierarchy)

rebuild_topictree = partial(base.rebuild_topictree, whitewash_node_data=whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=channel_data)