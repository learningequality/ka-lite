"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
from django.conf import settings
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy, string_concat

from .models import VideoLog, ExerciseLog, ContentLog
from fle_utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessageError, JsonResponseMessageWarning
from fle_utils.internet.webcache import backend_cache_page
from fle_utils.testing.decorators import allow_api_profiling

from kalite.topic_tools import get_flat_topic_tree, get_topic_tree

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
def topic_tree(request, channel):
    return JsonResponse(get_topic_tree(channel=channel))
