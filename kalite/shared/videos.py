import settings
import utils.videos  # keep access to all functions
from shared.topic_tools import get_topic_tree
from utils.videos import *  # get all into the current namespace, override some.


def get_video_ids_for_topic(topic_id, topic_tree=None):
    """Nobody actually calls this, just for utility when using the shell."""
    topic_tree = topic_tree or get_topic_tree()
    return utils.videos.get_video_ids_for_topic(topic_id, topic_tree)


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"
    return utils.videos.download_video(youtube_id, settings.CONTENT_ROOT, download_url, format, callback)


def delete_downloaded_files(youtube_id):
    return utils.videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)


def get_video_urls(video_id, format, video_on_disk=True):
    if not video_on_disk and settings.BACKUP_VIDEO_SOURCE:
        dict_vals = {"video_id": video_id, "video_format": format, "thumb_format": "png" }
        stream_url = settings.BACKUP_VIDEO_SOURCE % dict_vals
        thumbnail_url = settings.BACKUP_THUMBNAIL_SOURCE % dict_vals if settings.BACKUP_THUMBNAIL_SOURCE else None
        subtitles_url = None
    else:
        base_url = settings.CONTENT_URL + video_id
        stream_url = base_url + ".%s" % format
        thumbnail_url = base_url + ".png"
        subtitles_url = base_url + ".srt"

    return (stream_url, thumbnail_url, subtitles_url)
