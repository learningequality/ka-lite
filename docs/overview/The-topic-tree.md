The topic tree is a hierarchical tree of dictionaries, which define how different resources (videos and exercises) relate to each other.

Here's a snippet of the Khan Academy topic tree, as it appears in KA Lite:

![screen shot 2014-02-03 at 2 25 43 pm](https://f.cloud.github.com/assets/4072455/2070940/3584eddc-8d22-11e3-91d6-734f1b46e277.png)

## Overview

Topic tree data is stored in memory, so that any page requiring Khan Academy metadata can be generated quickly.  We also store details about the # of videos available, what their URLs are, and more!

Topic tree data would need to be reloaded when:
* # of videos change (on disk, or in the database)
* subtitles change (URLs need to be recomputed)

## Code

### Initial loading

The topic tree is loaded in `shared/topic_tools.py:get_topic_tree`.  
Additional properties are stamped on by:
    * `shared/videos.py:stamp_availability_on_topic` - stamps whether a topic is 'available'
    * `stamp_availability_on_video` - stamps on whether a video exists on disk (in any language).  Also optionally stamps on resource urls (video url, subtitle urls, thumbnail urls...)

### Reloading

When new videos are downloaded (or old ones deleted), the metadata within the topic tree needs to be reloaded.

The decorator `main/views.py:refresh_topic_cache` is the entry point in the code for a view to check on resources, to see if the topic tree data needs to be reloaded.  Each view that pulls data from the topic tree needs to add this decorator.

The main workhorse there is `main/views.py:refresh_topic_cache|refresh_topic_cache_wrapper_fn`, which examines a node (usually representing the requested page's position in the topic tree), and does all relevant checks for resource changes.

If the cache needs to be reloaded, then all relevant properties are deleted, and the function to compute those properties is called.

