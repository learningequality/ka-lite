import json
import os

import settings
from shared.videos import get_video_urls
from utils import topic_tools


TOPICS          = topic_tools.get_topic_tree()
NODE_CACHE      = topic_tools.get_node_cache()
ID2SLUG_MAP     = topic_tools.get_id2slug_map()

# Add initial video counts
(TOPICS,_,_) = topic_tools.get_video_counts(topic=TOPICS, videos_path=settings.CONTENT_ROOT)

# Compute video URLs
for video in NODE_CACHE["Video"].values():
    video["available"] = video["on_disk"] or bool(settings.BACKUP_VIDEO_SOURCE)
    (video["stream_url"], video["thumbnail_url"], video["subtitles_url"]) = get_video_urls(video["youtube_id"], "mp4", video["on_disk"])
