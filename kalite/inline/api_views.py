"""
Views accessible as an API endpoint for inline.  All should return JsonResponses.
"""
import yaml
import json

from fle_utils.internet.classes import JsonResponse


def narrative_view(request, narrative_id):
    f = open("kalite/inline/narratives.yaml", 'r')
    narrative_json = yaml.safe_load(f)
    f.close()

    print narrative_json
    return JsonResponse(narrative_json)
