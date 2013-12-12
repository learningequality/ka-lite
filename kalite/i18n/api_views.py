import datetime
import json
import os

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

import settings
from shared.decorators import central_server_only
from shared.i18n import LANGUAGE_PACK_AVAILABILITY_FILEPATH, SUBTITLES_DATA_ROOT, DUBBED_VIDEOS_MAPPING_FILEPATH
from utils.internet import allow_jsonp, api_handle_error_with_json, JsonResponse, JsonpResponse


@central_server_only
@allow_jsonp
@api_handle_error_with_json
def get_subtitle_counts(request):
    """
    Sort and return a dict in the following format that gives the count of srt files available by language:
        {"gu": {"count": 45, "name": "Gujarati"}, etc.. }
    """

    # Get the subtitles file
    if not os.path.exists(SUBTITLE_COUNTS_FILEPATH):
        # could call-command, but return 404 for now.
        raise Http404

    with open(SUBTITLE_COUNTS_FILEPATH, "r") as fp:
        subtitle_counts = json.load(fp)

    return JsonResponse(subtitle_counts)


@central_server_only
@allow_jsonp
@api_handle_error_with_json
def get_available_language_packs(request):
    """Return dict of available language packs"""

    # On central, loop through available language packs in static/language_packs/
    try:
        with open(LANGUAGE_PACK_AVAILABILITY_FILEPATH, "r") as fp:
            language_packs_available = json.load(fp)
    except:
        raise Http404
    return JsonResponse(sorted(language_packs_available.values(), key=lambda lp: lp["name"].lower()))

@central_server_only
@api_handle_error_with_json
def get_dubbed_video_mappings(request):
    """Return dict of available language packs"""

    # On central, loop through available language packs in static/language_packs/
    try:
        if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH):
            call_command("generate_dubbed_video_mappings")
        with open(DUBBED_VIDEOS_MAPPING_FILEPATH, "r") as fp:
            dubbed_videos_mapping = json.load(fp)
    except:
        raise Http404

    return JsonResponse(dubbed_videos_mapping)
