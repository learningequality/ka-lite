import datetime
import os

from django.http import HttpResponseRedirect, HttpResponse, Http404

import settings
from i18n import get_language_pack_filepath
from utils.django_utils import get_request_ip
from utils.videos import OUTSIDE_DOWNLOAD_BASE_URL  # for video download redirects

import stats_logger
from settings import LOG as logger  #temporary, while testing

logger = stats_logger()


# central server
def download_video(request, video_path):
    """Dummy function for capturing a video download request and logging
    to output, so we can collect stats."""

    # Log the info
    youtube_id = video_path.split(".")[0]
    logger.info("%s;%s;%s" % (get_request_ip(request), datetime.datetime.now(), youtube_id))

    # Redirect to amazon
    return HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + video_path)


# central server
def download_language_pack(request, version, lang_code):
    """Dummy function for capturing a language pack download request and logging
    to output, so we can collect stats."""

    # Log the event
    logger.info("%s;%s;%s;%s" % (get_request_ip(request), datetime.datetime.now(), lang_code, version))

    # Find the file to return
    zip_file = get_language_pack_filepath(lang_code, version=version)
    if not os.path.exists(zip_file):
        raise Http404

    # Stream it back to the user
    zh = open(zip_file,"rb")
    response = HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % (lang_code + ".zip")

    return response

# central server