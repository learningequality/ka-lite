import os

from django.http import HttpResponseRedirect, HttpResponse, Http404

import settings
from i18n import get_language_pack_filepath, get_srt_path
from utils.django_utils import get_request_ip
from utils.videos import OUTSIDE_DOWNLOAD_BASE_URL  # for video download redirects

from . import stats_logger
from version import VERSION


# central server
def download_video(request, video_path):
    """Dummy function for capturing a video download request and logging
    to output, so we can collect stats."""

    # Log the info
    youtube_id, file_ext = os.path.splitext(os.path.basename(video_path))
    if file_ext.lower() in [".mp4"]:
        stats_logger("videos").info("vd;%s;%s" % (get_request_ip(request), youtube_id))

    # Redirect to amazon
    return HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + video_path)


# central server
def download_language_pack(request, version, lang_code):
    """Dummy function for capturing a language pack download request and logging
    to output, so we can collect stats."""

    # Log the event
    stats_logger("language_packs").info("lpd;%s;%s;%s" % (get_request_ip(request), lang_code, version))

    # Find the file to return
    zip_filepath = get_language_pack_filepath(lang_code, version=version)
    if not os.path.exists(zip_filepath):
        raise Http404

    # Stream it back to the user
    zh = open(zip_filepath, "rb")
    response = HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(zip_filepath)

    return response


# central server
def download_subtitle(request, lang_code, youtube_id):
    """Dummy function for capturing a video download request and logging
    to output, so we can collect stats."""

    # Log the info
    stats_logger("subtitles").info("sd;%s;%s;%s" % (get_request_ip(request), lang_code, youtube_id))

    # Find the file to return
    srt_filepath = get_srt_path(lang_code, youtube_id=youtube_id)
    if not os.path.exists(srt_filepath):
        raise Http404

    # Stream it back to the user
    # Stream it back to the user
    zh = open(srt_filepath,"rb")
    response = HttpResponse(content=zh, mimetype='text/plain', content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(srt_filepath)

    return response


def download_windows_installer(request, version=VERSION):
    installer_name = "KALiteSetup-%s.exe" % version
    installer_url = settings.INSTALLER_BASE_URL + installer_name
    stats_logger("installer").info("wi;%s;%s" % (get_request_ip(request), installer_name))
    return HttpResponseRedirect(installer_url)
