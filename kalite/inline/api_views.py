"""
Views accessible as an API endpoint for inline.  All should return JsonResponses.
"""
import re

from django.utils.translation import ugettext as _

from fle_utils.internet.classes import JsonResponse, JsonResponseMessageWarning

from .narratives import NARRATIVES


def narrative_view(request, narrative_id):
    """
    :param request: the request
    :param narrative_id: the narrative id, a url to be matched
    :return: a serialized JSON blob of the narrative dict
    """
    the_narrative = {}
    for key, narr in NARRATIVES.iteritems():
        exp = re.compile(key)
        if exp.search(narrative_id):
            the_narrative[key] = narr
            break

    if not the_narrative:
        return JsonResponseMessageWarning(_("No inline help is available for this page."), status=404)

    return JsonResponse(the_narrative)
