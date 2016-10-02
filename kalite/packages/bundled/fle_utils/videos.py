"""
"""
import glob
import logging
import os
import socket

from general import ensure_dir
from internet.download import callback_percent_proxy, download_file, URLNotFound, DownloadCancelled

OUTSIDE_DOWNLOAD_BASE_URL = "http://s3.amazonaws.com/KA-youtube-converted/"  # needed for redirects
OUTSIDE_DOWNLOAD_URL = OUTSIDE_DOWNLOAD_BASE_URL + "%s/%s"  # needed for default behavior, below

logger = logging.getLogger(__name__)


def get_outside_video_urls(youtube_id, download_url=OUTSIDE_DOWNLOAD_URL, format="mp4"):

    video_filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    url = download_url % (video_filename, video_filename)

    thumb_filename = "%(id)s.png" % {"id": youtube_id}
    thumb_url = download_url % (video_filename, thumb_filename)

    return (url, thumb_url)


def download_video(youtube_id, download_path="../content/", download_url=OUTSIDE_DOWNLOAD_URL, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    ensure_dir(download_path)

    url, thumb_url = get_outside_video_urls(youtube_id, download_url=download_url, format=format)
    video_filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    filepath = os.path.join(download_path, video_filename)

    thumb_filename = "%(id)s.png" % {"id": youtube_id}
    thumb_filepath = os.path.join(download_path, thumb_filename)

    try:
        response = download_file(url, filepath, callback_percent_proxy(callback, end_percent=95))
        if (
                not os.path.isfile(filepath) or
                "content-length" not in response.headers or
                not len(open(filepath, "rb").read()) == int(response.headers['content-length'])):
            raise URLNotFound("Video was not found, tried: {}".format(url))

        response = download_file(thumb_url, thumb_filepath, callback_percent_proxy(callback, start_percent=95, end_percent=100))
        if (
                not os.path.isfile(thumb_filepath) or
                "content-length" not in response.headers or
                not len(open(thumb_filepath, "rb").read()) == int(response.headers['content-length'])):
            raise URLNotFound("Thumbnail was not found, tried: {}".format(thumb_url))

    except DownloadCancelled:
        delete_downloaded_files(youtube_id, download_path)
        raise

    except (socket.timeout, IOError) as e:
        logging.exception(e)
        logging.info("Timeout -- Network UnReachable")
        delete_downloaded_files(youtube_id, download_path)
        raise

    except Exception as e:
        logging.exception(e)
        delete_downloaded_files(youtube_id, download_path)
        raise


def delete_downloaded_files(youtube_id, download_path):
    files_deleted = 0
    for filepath in glob.glob(os.path.join(download_path, youtube_id + ".*")):
        try:
            os.remove(filepath)
            files_deleted += 1
        except OSError:
            pass
    if files_deleted:
        return True
