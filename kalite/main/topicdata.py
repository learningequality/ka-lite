import json
import os

import settings
from shared import topic_tools
from shared.videos import get_video_urls, get_video_counts


TOPICS          = topic_tools.get_topic_tree()
NODE_CACHE      = topic_tools.get_node_cache()
ID2SLUG_MAP     = topic_tools.get_id2slug_map()

# Add initial video counts
get_video_counts(topic=TOPICS, videos_path=settings.CONTENT_ROOT)

# Compute video URLs.  Must use videos from topics, as the NODE_CACHE doesn't contain all video objects. :-/
for video in topic_tools.get_topic_videos(path="/"):
    video["available"] = video["on_disk"] or bool(settings.BACKUP_VIDEO_SOURCE)
    (video["stream_url"], video["thumbnail_url"], video["subtitles_url"]) = get_video_urls(video["youtube_id"], "mp4", video["on_disk"])

