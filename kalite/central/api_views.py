import json
import os

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError

from utils.decorators import require_admin_api
from utils.internet import JsonResponse

import settings


def get_subtitle_counts(request):
    """
    Sort and return a dict in the following format that gives the count of srt files available by language:
        {"gu": {"count": 45, "name": "Gujarati"}, etc.. }
    """

    # Get the subtitles file
    subtitledata_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/subtitledata/"
    if not os.path.exists(subtitledata_path):
        # could call-command, but return 404 for now.
        raise Http404
    subtitle_counts = json.loads(open(subtitledata_path + "subtitle_counts.json").read())


    # Return an appropriate response
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

def download_subtitle_zip(request, locale):
    """
    Return a zip of the subtitles for the correct locale
    """

    zip_file = "%s/subtitles/%s_subtitles.zip" % (settings.MEDIA_ROOT, locale)  
    if not os.path.exists(zip_file):
        # could call_command, but return 404 for now
        raise Http404

    zh = open(zip_file, "rb")
    return HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')
