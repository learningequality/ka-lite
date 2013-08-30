import datetime
import json
import os
from collections import OrderedDict
from decorator.decorator import decorator

from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

import kalite
import settings
import version
from .models import Organization, get_or_create_user_profile
from .views import get_central_server_host
from securesync.models import Zone
from utils.internet import allow_jsonp, api_handle_error_with_json, JsonResponse


@allow_jsonp
@api_handle_error_with_json
def get_kalite_version(request):
    assert kalite.VERSION in version.VERSION_INFO

    request_version = request.GET.get("current_version", "0.10.0")  # default to first version that can understand this.
    needed_updates = [v for v in sorted(version.VERSION_INFO.keys()) if request_version < v]    # versions are nice--they sort by string
    return JsonResponse({
        "version": kalite.VERSION,
        "version_info": OrderedDict([(v, version.VERSION_INFO[v]) for v in needed_updates]),
    })


@allow_jsonp
@api_handle_error_with_json
def get_download_urls(request):
    base_url = "%s://%s" % ("https" if request.is_secure() else "http", get_central_server_host(request))

    # TODO: once Dylan makes all subtitle languages available,
    #   don't hard-code this.
    download_sizes = {
        "en": 19.8,
    }

    downloads = {}
    for locale, size in download_sizes.iteritems():
        urlargs = {
            "version": kalite.VERSION,
            "platform": "all",
            "locale": locale
        }
        downloads[locale] = {
            "display_name": "",  # Will fill in when language list from subtitles is available.
            "size": size,
            "url": "%s%s" % (base_url, reverse("download_kalite_public", kwargs=urlargs)),
        }

    return JsonResponse(downloads)


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


    # Return an appropriate response
    # TODO(dylan): Use jsonp decorator once it becomes available
    if request.GET.get("callback",None):
        # JSONP response
        response = HttpResponse("%s(%s);" % (request.GET["callback"], json.dumps(subtitle_counts, sort_keys=True)))
        response["Access-Control-Allow-Headers"] = "*"
        response["Content-Type"] = "text/javascript"
        return response

    else:
        # Regular request
        response = JsonResponse(json.dumps(subtitle_counts, sort_keys=True), status=200)
        return response
