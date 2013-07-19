import json
import os

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError

from utils.decorators import require_admin_api
from utils.internet import JsonResponse

import settings


@require_admin_api
def get_subtitle_counts(request):
	"""Sort and return a dict in the following format that gives the count of srt files available by language:
		{"gu": {"count": 45, "name": "Gujarati"}, etc.. }
	"""
	subtitledata_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/subtitledata/"
	subtitle_counts = json.loads(open(subtitledata_path + "subtitle_counts.json").read())
	return JsonResponse(json.dumps(subtitle_counts, sort_keys=True), status=200)


def download_subtitle_zip(request, locale):
	"""Return a zip of the subtitles for the correct locale"""
	import pdb; pdb.set_trace()
	zip_file = "%s/subtitles/%s_subtitles.zip" % (settings.MEDIA_ROOT, locale)  
	zh = open(zip_file, "rb")
	return HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')