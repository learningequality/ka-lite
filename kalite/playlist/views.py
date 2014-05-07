import json
import os

from fle_utils.internet import JsonResponse, api_handle_error_with_json


def sample_json(request):
	jsonfile = os.path.join(os.path.dirname(__file__), 'test_playlist.json')
	with open(jsonfile) as f:
		return JsonResponse(json.load(f))