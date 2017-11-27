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
from requests.exceptions import HTTPError


logger = logging.getLogger(__name__)


def get_local_video_size(youtube_id, default=None):
    try:
        return os.path.getsize(os.path.join(django_settings.CONTENT_ROOT, "%s.mp4" % youtube_id))
    except (IOError, OSError) as e:
        logger.exception(e)
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

    logger.info(
        "Downloading {id} (video: {video}, thumbnail: {thumbnail})".format(
            id=youtube_id,
            video=url,
            thumbnail=thumb_url,
        )
    )

    # Download video
    try:
        download_file(
            url,
            dst=filepath,
            callback=callback_percent_proxy(callback, end_percent=95),
            max_retries=settings.DOWNLOAD_MAX_RETRIES
        )
    except HTTPError as e:
        logger.error(
            "HTTP status {status} for URL: {url}".format(
                status=e.response.status_code,
                url=e.response.url,
            )
        )
        raise

    except (socket.timeout, IOError) as e:
        logger.error("Network error for URL: {url}, exception: {exc}".format(
            url=url,
            exc=str(e)
        ))
        delete_downloaded_files(youtube_id)
        raise

    except Exception as e:
        logger.exception(e)
        delete_downloaded_files(youtube_id)
        raise

    # Download thumbnail - don't fail if it doesn't succeed, because at this
    # stage, we know that the video has been downloaded.
    try:
        download_file(
            thumb_url,
            dst=thumb_filepath,
            callback=callback_percent_proxy(callback, start_percent=95, end_percent=100),
            max_retries=settings.DOWNLOAD_MAX_RETRIES
        )
    except HTTPError as e:
        logger.error(
            "HTTP status {status} for URL: {url}".format(
                status=e.response.status_code,
                url=e.response.url,
            )
        )
    except (socket.timeout, IOError) as e:
        logger.error("Network error for URL: {url}, exception: {exc}".format(
            url=url,
            exc=str(e)
        ))


def delete_downloaded_files(youtube_id):
    download_path = django_settings.CONTENT_ROOT
    files_deleted = 0
    for filepath in glob.glob(os.path.join(download_path, youtube_id + ".*")):
        if os.path.isfile(filepath):
            os.remove(filepath)
            files_deleted += 1
    if files_deleted:
        return True
