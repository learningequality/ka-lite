"""
"""
import os

from django.conf import settings
logging = settings.LOG

from fle_utils import videos  # keep access to all functions


def get_local_video_size(youtube_id, default=None):
    try:
        return os.path.getsize(os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id))
    except Exception as e:
        logging.debug(str(e))
        return default


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"
    return videos.download_video(youtube_id, settings.CONTENT_ROOT, download_url, format, callback)


def delete_downloaded_files(youtube_id):
    return videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)
