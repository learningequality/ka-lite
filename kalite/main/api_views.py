"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
from django.conf import settings
from django.http import Http404
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy, string_concat

from .models import VideoLog, ExerciseLog, ContentLog
from fle_utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessageError, JsonResponseMessageWarning
from fle_utils.internet.webcache import backend_cache_page
from fle_utils.testing.decorators import allow_api_profiling

from kalite.topic_tools import get_flat_topic_tree, get_node_cache

class student_log_api(object):
    """
    Decorator (wrapper) for telling the user what happens
    in the case that they're not logged in (or other issues
    with using the API endpoint)
    """

    def __init__(self, logged_out_message):
        self.logged_out_message = logged_out_message

    def __call__(self, handler):
        @api_handle_error_with_json
        def student_log_api_wrapper_fn(request, *args, **kwargs):
            # TODO(bcipolli): send user info in the post data,
            #   allowing cross-checking of user information
            #   and better error reporting
            if "facility_user" not in request.session:
                return JsonResponseMessageWarning(string_concat(self.logged_out_message, "  ", ugettext_lazy("You must be logged in as a student or teacher to view/save progress.")))
            else:
                return handler(request, *args, **kwargs)
        return student_log_api_wrapper_fn


# TODO(rtibbles): Refactor client side code for status rendering in knowledge map and topic pages
# to use a more RESTful API call.
@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Progress not loaded."))
def get_exercise_logs(request):
    """
    Given a list of exercise_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponseMessageError(_("Could not load ExerciseLog objects: Unrecognized input data format."))

    user = request.session["facility_user"]
    logs = ExerciseLog.objects \
            .filter(user=user, exercise_id__in=data) \
            .values("exercise_id", "streak_progress", "complete", "points", "struggling", "attempts")
    return JsonResponse(list(logs))


@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Progress not loaded."))
def get_video_logs(request):
    """
    Given a list of video_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.body or "[]")
    if not isinstance(data, list):
        return JsonResponseMessageError(_("Could not load VideoLog objects: Unrecognized input data format."))

    user = request.session["facility_user"]
    logs = VideoLog.objects \
        .filter(user=user, video_id__in=data) \
        .values("video_id", "complete", "total_seconds_watched", "points")

    return JsonResponse(list(logs))

@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Progress not loaded."))
def get_content_logs(request):
    """
    Given a list of content_ids, retrieve a list of content logs for this user.
    """
    data = simplejson.loads(request.body or "[]")
    if not isinstance(data, list):
        return JsonResponseMessageError(_("Could not load ContentLog objects: Unrecognized input data format."))

    user = request.session["facility_user"]
    logs = ContentLog.objects \
        .filter(user=user, content_id__in=data) \
        .values("content_id", "complete", "points")

    return JsonResponse(list(logs))


@api_handle_error_with_json
@backend_cache_page
def flat_topic_tree(request, lang_code):
    return JsonResponse(get_flat_topic_tree(lang_code=lang_code))


@api_handle_error_with_json
@backend_cache_page
def knowledge_map_json(request, topic_id):
    """
    Topic nodes can now have a "knowledge_map" stamped on them.
    This code currently exposes that data to the kmap-editor code,
    mostly as it expects it now.

    So this is kind of a hack-ish mix of code that avoids rewriting kmap-editor.js,
    but allows a cleaner rewrite of the stored data, and bridges the gap between
    that messiness and the cleaner back-end.
    """

    # Try and get the requested topic, and make sure it has knowledge map data available.
    topic = get_node_cache("Topic").get(topic_id)
    if not topic:
        raise Http404("Topic '%s' not found" % topic_id)
    elif not "knowledge_map" in topic:
        raise Http404("Topic '%s' has no knowledge map metadata." % topic_id)

    # For each node (can be of any type now), pull out only
    #   the relevant data.
    kmap = topic["knowledge_map"]
    nodes_out = {}
    for id, kmap_data in kmap["nodes"].iteritems():
        cur_node = get_node_cache(kmap_data["kind"])[id]
        nodes_out[id] = {
            "id": cur_node["id"],
            "title": _(cur_node["title"]),
            "h_position":  kmap_data["h_position"],
            "v_position": kmap_data["v_position"],
            "icon_url": cur_node.get("icon_url", cur_node.get("icon_src")),  # messy
            "path": cur_node["path"],
        }
        if not "polylines" in kmap:  # messy
            # Two ways to define lines:
            # 1. have "polylines" defined explicitly
            # 2. use prerequisites to compute lines on the fly.
            nodes_out[id]["prerequisites"] = cur_node.get("prerequisites", [])

    return JsonResponse({
        "nodes": nodes_out,
        "polylines": kmap.get("polylines"),  # messy
    })
