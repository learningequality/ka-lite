import re
import json
import sys
import os

from utils.internet import JsonResponse

subtitledata_path = os.path.dirname(os.path.realpath(
    __file__)) + "/../static/data/subtitledata/"

def get_subtitle_counts(request):
	"""Return a dict in the following format that gives the count of srt files available by language:
		{"gu": {"count": 45, "name": "Gujarati"}, etc.. }
	"""
 	subtitle_counts = json.loads(open(subtitledata_path + "subtitle_counts.json").read())
 	return JsonResponse(subtitle_counts, status=200)
