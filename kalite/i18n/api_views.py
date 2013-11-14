import datetime
import json
import os

from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

import settings
from shared.decorators import central_server_only
from utils.internet import allow_jsonp, api_handle_error_with_json, JsonResponse, JsonpResponse
from i18n.management.commands.update_language_packs import LANGUAGE_PACK_AVAILABILITY_FILENAME


@central_server_only
@allow_jsonp
@api_handle_error_with_json
def get_subtitle_counts(request):
    """
    Sort and return a dict in the following format that gives the count of srt files available by language:
        {"gu": {"count": 45, "name": "Gujarati"}, etc.. }
    """

    # Get the subtitles file
    subtitledata_path = settings.SUBTITLES_DATA_ROOT
    if not os.path.exists(subtitledata_path):
        # could call-command, but return 404 for now.
        raise Http404
    subtitle_counts = json.loads(open(subtitledata_path + "subtitle_counts.json").read())

    return JsonResponse(json.dumps(subtitle_counts, sort_keys=True))


@central_server_only
@allow_jsonp
@api_handle_error_with_json
def get_available_language_packs(request):
    """Return dict of available language packs"""

    # On central, loop through available language packs in static/language_packs/
    language_packs_path = settings.LANGUAGE_PACK_ROOT
    try:
        language_packs_available = json.loads(open(os.path.join(language_packs_path, LANGUAGE_PACK_AVAILABILITY_FILENAME)).read())
    except:
        raise Http404

    return JsonResponse(language_packs_available)
