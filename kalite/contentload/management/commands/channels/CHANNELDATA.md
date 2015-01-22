slug_key is a mapping for different data kinds, showing which attribute to use to define the slug.
This slug will be used to build the resource path in the URL.

```
slug_key = {
    "Topic": "node_slug",
}
```

title_key is a mapping for different data kinds, showing which attribute to use to define the title.

```
title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
    "AssessmentItem": "name"
}
```

id_key is a mapping for different data kinds, showing which attribute to use to define the id.
This is deprecated for content import.

```
id_key = {
    "Topic": "node_slug",
    "Video": "youtube_id",
    "Exercise": "name",
    "AssessmentItem": "id"
}
```

These are Khan Academy specific data that allows us to download their icons.
Deprecated with the latest knowledge map.

```
iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"
```

Determines what attributes should be retained (both from the API resource, and from processing of data).
If a property is not here, it will not appear in the relevant nodecache for that content type.
```
attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "y_pos", "x_pos", "icon_src", "child_data", "render_type", "path", "slug"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id", "y_pos", "x_pos", "in_knowledge_map", "path", "slug"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "y_pos", "x_pos", "in_knowledge_map", "all_assessment_items", "uses_assessment_items", "path", "slug"],
    "AssessmentItem": ["kind", "name", "item_data", "tags", "author_names", "sha", "id"]
}
```

Determines what attributes are left in the denormalized representation of content in the topic tree.
```
denormed_attribute_list = {
    "Video": ["kind", "description", "title", "id", "slug"],
    "Exercise": ["kind", "description", "title", "id", "slug"],
    "Audio": ["kind", "description", "title", "id", "slug"]
}
```

Khan Academy has several content kinds that we cannot use, so we just filter out their data by excluding these kinds.
```
kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]
```

Some content we cannot use due to copyright concerns, so we exclude these specific slugs for that reason.
```
slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res", "MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "cs", "cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math", "cc-seventh-grade-math", "cc-eighth-grade-math", "hour-of-code"]
```

Attributes that are OK for a while, but need to be scrubbed off before we save the cache files.
```
temp_ok_atts = ["x_pos", "y_pos", "icon_src", u'topic_page_url']
```