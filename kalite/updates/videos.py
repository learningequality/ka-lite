"""
"""
import glob
import logging
import os
import socket

from . import settings

from django.conf import settings as django_settings
from fle_utils.general import ensure_dir
from fle_utils.internet.download import callback_percent_proxy, download_file


logger = logging.getLogger(__name__)


def get_local_video_size(youtube_id, default=None):
    try:
        return os.path.getsize(os.path.join(django_settings.CONTENT_ROOT, "%s.mp4" % youtube_id))
    except Exception as e:
        logger.debug(str(e))
        return default


def get_url_pattern():
    """
    Returns a pattern for generating URLs of videos and thumbnails
    """
    base = "http://{}/download/videos/".format(django_settings.CENTRAL_SERVER_HOST)
    return base + "{dir}/{filename}"


def get_video_filename(youtube_id, extension="mp4"):
    return "%(id)s.%(format)s" % {"id": youtube_id, "format": extension}


def get_video_url(youtube_id, extension="mp4"):
    filename = get_video_filename(youtube_id, extension)
    return get_url_pattern().format(
        dir=filename,
        filename=filename
    )
    

def get_thumbnail_filename(youtube_id):
    return "%(id)s.png" % {"id": youtube_id}


def get_thumbnail_url(youtube_id, video_extension="mp4"):
    return get_url_pattern().format(
        dir=get_video_filename(youtube_id, video_extension),
        filename=get_thumbnail_filename(youtube_id)
    )


def get_video_local_path(youtube_id, extension="mp4"):
    download_path=django_settings.CONTENT_ROOT
    filename = get_video_filename(youtube_id, extension)
    return os.path.join(download_path, filename)


def get_thumbnail_local_path(youtube_id):
    download_path=django_settings.CONTENT_ROOT
    filename = get_thumbnail_filename(youtube_id)
    return os.path.join(download_path, filename)


def download_video(youtube_id, extension="mp4", callback=None):
    """
    Downloads video file to disk
    """

    ensure_dir(django_settings.CONTENT_ROOT)

    url = get_video_url(youtube_id, extension)
    thumb_url = get_thumbnail_url(youtube_id, extension)

    filepath = get_video_local_path(youtube_id, extension)
    thumb_filepath = get_thumbnail_local_path(youtube_id)

    try:
        # Download video
        download_file(
            url,
            dst=filepath,
            callback=callback_percent_proxy(callback, end_percent=95),
            max_retries=settings.DOWNLOAD_MAX_RETRIES
        )

        # Download thumbnail
        download_file(
            thumb_url,
            dst=thumb_filepath,
            callback=callback_percent_proxy(callback, start_percent=95, end_percent=100),
            max_retries=settings.DOWNLOAD_MAX_RETRIES
        )

    except (socket.timeout, IOError) as e:
        logger.exception(e)
        logger.info("Timeout -- Network UnReachable")
        delete_downloaded_files(youtube_id)
        raise

    except Exception as e:
        logger.exception(e)
        delete_downloaded_files(youtube_id)
        raise


def delete_downloaded_files(youtube_id):
    download_path = django_settings.CONTENT_ROOT
    files_deleted = 0
    for filepath in glob.glob(os.path.join(download_path, youtube_id + ".*")):
        try:
            os.remove(filepath)
            files_deleted += 1
        except OSError:
            pass
    if files_deleted:
        return True
