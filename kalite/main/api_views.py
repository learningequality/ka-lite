"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse
from fle_utils.internet.webcache import backend_cache_page

from kalite.topic_tools.api import get_flat_topic_tree, get_topic_tree

@api_handle_error_with_json
@backend_cache_page
def flat_topic_tree(request, lang_code):
    return JsonResponse(get_flat_topic_tree(lang_code=lang_code))

@api_handle_error_with_json
@backend_cache_page
def topic_tree(request, channel):
    return JsonResponse(get_topic_tree(channel=channel, language=request.language))
