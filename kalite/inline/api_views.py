"""
Views accessible as an API endpoint for inline.  All should return JsonResponses.
"""
import os

from kalite.shared.utils import open_json_or_yml
from kalite import settings

from fle_utils.internet.classes import JsonResponse


def narrative_view(request, narrative_id):
    filename = os.path.join(settings.CONTENT_DATA_PATH, "narratives")
    narrative_json = open_json_or_yml(filename)
    # TODO(MCGallaspy): This is incomplete. Needs to use the narrative_id.
    return JsonResponse(narrative_json)
