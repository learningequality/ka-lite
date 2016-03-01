"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _

from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError

from kalite.topic_tools.content_models import get_topic_nodes, get_content_item, search_topic_nodes, get_assessment_item_data
from kalite.topic_tools.content_recommendation import get_resume_recommendations, get_next_recommendations, get_explore_recommendations
from kalite.facility.models import FacilityUser
from kalite.distributed.api_views import get_messages_for_api_calls

@api_handle_error_with_json
def topic_tree(request, channel):
    parent = request.GET.get("parent")
    return JsonResponse(get_topic_nodes(channel=channel, language=request.language, parent=parent))


@api_handle_error_with_json
def search_api(request, channel):
    query = request.GET.get("term")
    if query is None:
        return JsonResponseMessageError("No search term specified", status=404)

    query = query.lower()
    # search for topic, video or exercise with matching title

    matches, exact, pages = search_topic_nodes(query=query, channel=channel, language=request.language, page=1, items_per_page=15, exact=False)

    if not matches:
        messages.warning(request, _("Search completed, no content was found for your search. Try something else."))

    return JsonResponse(matches)


@api_handle_error_with_json
def content_item(request, channel, content_id):
    language = request.language

    content = get_content_item(channel=channel, content_id=content_id, language=language)

    if not content:
        content = {
            "title": "Unavailable Content",
            "description": "This content is unavailable. Either it must be downloaded, or the url is incorrect.",
            "available": False,
            "kind": "Video",
            "id": "unavailable_content",
            "slug": "unavailable_content",
            "path": "unavailable_content"
        }

    if not content.get("available", False):
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this content in the topic tree
            messages.warning(request, _("This content was not found! You can download it by going to the Manage > Videos page."))
        elif request.is_logged_in:
            messages.warning(request, _("This content was not found! Please contact your coach or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This content was not found! You must login as an admin/coach to download the content."))

    content["messages"] = get_messages_for_api_calls(request)

    return JsonResponse(content)


@api_handle_error_with_json
def content_recommender(request):
    """Populate response with recommendation(s)"""

    user_id = request.GET.get('user')
    user = request.session.get('facility_user')

    if not user:
        if request.user.is_authenticated() and request.user.is_superuser:
            user = get_object_or_404(FacilityUser, pk=user_id)
        else:
            return JsonResponseMessageError("You are not authorized to view these recommendations.", status=401)

    resume = request.GET.get('resume')
    next = request.GET.get('next')
    explore = request.GET.get('explore')

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


@api_handle_error_with_json
def assessment_item(request, assessment_item_id):
    assessment_item_dict = get_assessment_item_data(channel=getattr(request, "channel", "khan"),
                                                    language=getattr(request, "language", "en"),
                                                    assessment_item_id=assessment_item_id)
    return JsonResponse(assessment_item_dict)
