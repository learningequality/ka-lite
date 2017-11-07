"""
"""
import glob
import logging
import os
import socket

from django.conf import settings
from fle_utils.general import ensure_dir
from fle_utils.internet.download import callback_percent_proxy, download_file, URLNotFound, DownloadCancelled


logger = logging.getLogger(__name__)


def get_local_video_size(youtube_id, default=None):
    try:
        return os.path.getsize(os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id))
    except Exception as e:
        logger.debug(str(e))
        return default


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"

    download_path=settings.CONTENT_ROOT
    
    ensure_dir(download_path)

    video_filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    thumb_filename = "%(id)s.png" % {"id": youtube_id}

    url = download_url % (video_filename, video_filename)
    thumb_url = download_url % (video_filename, thumb_filename)

    filepath = os.path.join(download_path, video_filename)
    thumb_filepath = os.path.join(download_path, thumb_filename)

    try:
        response = download_file(url, filepath, callback_percent_proxy(callback, end_percent=95))
        if (
                not os.path.isfile(filepath) or
                "content-length" not in response.headers or
                not os.path.getsize(filepath) == int(response.headers['content-length'])):
            raise URLNotFound("Video was not found, tried: {}".format(url))

        response = download_file(thumb_url, thumb_filepath, callback_percent_proxy(callback, start_percent=95, end_percent=100))
        if (
                not os.path.isfile(thumb_filepath) or
                "content-length" not in response.headers or
                not os.path.getsize(thumb_filepath) == int(response.headers['content-length'])):
            raise URLNotFound("Thumbnail was not found, tried: {}".format(thumb_url))

    except DownloadCancelled:
        delete_downloaded_files(youtube_id, download_path)
        raise

    except (socket.timeout, IOError) as e:
        logger.exception(e)
        logger.info("Timeout -- Network UnReachable")
        delete_downloaded_files(youtube_id, download_path)
        raise

    except Exception as e:
        logger.exception(e)
        delete_downloaded_files(youtube_id, download_path)
        raise


def delete_downloaded_files(youtube_id):
    download_path = settings.CONTENT_ROOT
    files_deleted = 0
    for filepath in glob.glob(os.path.join(download_path, youtube_id + ".*")):
        try:
            os.remove(filepath)
            files_deleted += 1
        except OSError:
            pass
    if files_deleted:
        return True
