import datetime
import json
import os

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

import settings
from . import get_language_pack_availability_filepath, SUBTITLE_COUNTS_FILEPATH, SUBTITLES_DATA_ROOT, DUBBED_VIDEOS_MAPPING_FILEPATH
from settings import LOG as logging
from testing.asserts import central_server_only
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
        raise Http404("Subtitles count file %s not found." % SUBTITLE_COUNTS_FILEPATH)

    with open(SUBTITLE_COUNTS_FILEPATH, "r") as fp:
        subtitle_counts = json.load(fp)

    return JsonResponse(subtitle_counts)


@central_server_only
@allow_jsonp
@api_handle_error_with_json
def get_available_language_packs(request, version):
    """Return dict of available language packs"""

    # On central, loop through available language packs in static/language_packs/
    try:
        with open(get_language_pack_availability_filepath(version=version), "r") as fp:
            language_packs_available = json.load(fp)
    except Exception as e:
        logging.debug("Unexpected error getting available language packs: %s" % e)
        language_packs_available = {}
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
