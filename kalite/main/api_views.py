"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
from django.shortcuts import get_object_or_404

from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError

from kalite.topic_tools import get_topic_tree
from kalite.topic_tools.content_recommendation import get_resume_recommendations, get_next_recommendations, get_explore_recommendations
from kalite.facility.models import FacilityUser

@api_handle_error_with_json
def topic_tree(request, channel):
    parent = request.GET.get("parent")
    return JsonResponse(get_topic_tree(channel=channel, language=request.language, parent=parent))

@api_handle_error_with_json
def content_recommender(request):
    """Populate response with recommendation(s)"""

    user_id = request.GET.get('user', None)
    user = request.session.get('facility_user')

    if not user:
        if request.user.is_authenticated() and request.user.is_superuser:
            user = get_object_or_404(FacilityUser, pk=user_id)
        else:
            return JsonResponseMessageError("You are not authorized to view these recommendations.", status=401)

    resume = request.GET.get('resume', None)
    next = request.GET.get('next', None)
    explore = request.GET.get('explore', None)

    def set_bool_flag(flag_name, rec_dict):
        rec_dict[flag_name] = True
        return rec_dict

    # retrieve resume recommendation(s) and set resume boolean flag
    resume_recommendations = [set_bool_flag("resume", rec) for rec in get_resume_recommendations(user, request)] if resume else []

    # retrieve next_steps recommendations, set next_steps boolean flag, and flatten results for api response
    next_recommendations = [set_bool_flag("next", rec) for rec in get_next_recommendations(user, request)] if next else []

    # retrieve explore recommendations, set explore boolean flag, and flatten results for api response
    explore_recommendations = [set_bool_flag("explore", rec) for rec in get_explore_recommendations(user, request)] if explore else []

    return JsonResponse(resume_recommendations + next_recommendations + explore_recommendations)