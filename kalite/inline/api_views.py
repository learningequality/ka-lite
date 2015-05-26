"""
Views accessible as an API endpoint for inline.  All should return JsonResponses.
"""
import os
import re

from kalite.shared.utils import open_json_or_yml
from kalite import settings

from fle_utils.internet.classes import JsonResponse


def narrative_view(request, narrative_id):
    """
    :param request: the request
    :param narrative_id: the narrative id, a url to be matched
    :return: a serialized JSON blob of the narrative dict
    """
    filename = os.path.join(settings.CONTENT_DATA_PATH, "narratives")
    narratives = open_json_or_yml(filename)
    the_narrative = {}
    for key, narr in narratives.iteritems():
        exp = re.compile(key)
        if exp.search(narrative_id):
            the_narrative[key] = narr
            break
    return JsonResponse(the_narrative)
