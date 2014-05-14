import json
import os

from fle_utils.internet import JsonResponse
from annoying.decorators import render_to


def sample_json(request):
    jsonfile = os.path.join(os.path.dirname(__file__), 'test_playlist.json')
    with open(jsonfile) as f:
        return JsonResponse(json.load(f))


@render_to("playlist/index.html")
def playlists(request):
    context = {
        "title": "Playlists",
    }
    return context
