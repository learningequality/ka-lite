import json
import os

import settings
from shared import topic_tools
from shared.i18n import get_installed_subtitles
from shared.videos import get_video_urls, get_video_counts


TOPICS          = topic_tools.get_topic_tree()
NODE_CACHE      = topic_tools.get_node_cache()
SLUG2ID_MAP     = topic_tools.get_slug2id_map()

# Add initial video counts
get_video_counts(topic=TOPICS, videos_path=settings.CONTENT_ROOT)

# Compute video URLs.  Must use videos from topics, as the NODE_CACHE doesn't contain all video objects. :-/
for video in topic_tools.get_topic_videos(path="/"):
    video["available"] = video["on_disk"] or bool(settings.BACKUP_VIDEO_SOURCE)
    language_codes = get_installed_subtitles(video["youtube_id"])
    (video["stream_url"], video["thumbnail_url"], video["subtitles_urls"]) = get_video_urls(
        video_id=video["id"],
        youtube_id=video["youtube_id"],
        format="mp4",
        video_on_disk=video["on_disk"],
        language_codes=language_codes,
    )

