"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET/save student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
import json

from annoying.functions import get_object_or_None
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy, string_concat

from .api_forms import ExerciseLogForm, VideoLogForm, AttemptLogForm
from .models import VideoLog, ExerciseLog, AttemptLog, ContentLog
from fle_utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessageSuccess, JsonResponseMessageError, JsonResponseMessageWarning
from fle_utils.internet.webcache import backend_cache_page
from fle_utils.testing.decorators import allow_api_profiling

from kalite.topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes, get_exercise_data, get_video_data, get_assessment_item_data

from kalite.dynamic_assets.decorators import dynamic_settings

from kalite.student_testing.utils import get_current_unit_settings_value
from kalite.playlist.models import VanillaPlaylist as Playlist


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


@student_log_api(logged_out_message=ugettext_lazy("Video progress not saved."))
def save_video_log(request):
    """
    Receives a video_id and relevant data,
    saves it to the currently authorized user.
    """

    # Form does all the data validation, including the video_id
    form = VideoLogForm(data=simplejson.loads(request.body))
    if not form.is_valid():
        raise ValidationError(form.errors)
    data = form.data
    user = request.session["facility_user"]
    try:
        complete = data.get("complete", False)
        completion_timestamp = data.get("completion_timestamp", None)
        videolog = VideoLog.update_video_log(
            facility_user=user,
            video_id=data["video_id"],
            youtube_id=data["youtube_id"],
            total_seconds_watched=data["total_seconds_watched"],  # don't set incrementally, to avoid concurrency issues
            points=data["points"],
            language=data.get("language") or request.language,
            complete=complete,
            completion_timestamp=completion_timestamp,
        )

    except ValidationError as e:
        return JsonResponseMessageError(_("Could not save VideoLog: %(err)s") % {"err": e})

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed

    return JsonResponse({
        "points": videolog.points,
        "complete": videolog.complete,
    })

@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Exercise progress not logged."))
def exercise_log(request, exercise_id):

    if request.method == "POST":
        """
        Receives an exercise_id and relevant data,
        saves it to the currently authorized user.
        """

        # Form does all data validation, including of the exercise_id
        form = ExerciseLogForm(data=simplejson.loads(request.raw_post_data))
        if not form.is_valid():
            raise Exception(form.errors)
        data = form.data

        # More robust extraction of previous object
        user = request.session["facility_user"]
        (exerciselog, was_created) = ExerciseLog.get_or_initialize(user=user, exercise_id=exercise_id)

        exerciselog.attempts = data["attempts"]  # don't increment, because we fail to save some requests
        exerciselog.streak_progress = data["streak_progress"]
        exerciselog.points = data["points"]
        exerciselog.language = data.get("language") or request.language

        try:
            exerciselog.full_clean()
            exerciselog.save()
        except ValidationError as e:
            return JsonResponseMessageError(_("Could not save ExerciseLog") + u": %s" % e)

        if "points" in request.session:
            del request.session["points"]  # will be recomputed when needed

        # Special message if you've just completed.
        #   NOTE: it's important to check this AFTER calling save() above.
        # TODO (rtibbles): MOVE THIS TO THE CLIENT SIDE!
        if not previously_complete and exerciselog.complete:
            exercise = get_node_cache("Exercise").get(data["exercise_id"], None)
            junk, next_exercise = get_neighbor_nodes(exercise, neighbor_kind="Exercise") if exercise else None
            if not next_exercise:
                return JsonResponseMessageSuccess(_("You have mastered this exercise and this topic!"))
            else:
                return JsonResponseMessageSuccess(_("You have mastered this exercise!  Please continue on to <a href='%(href)s'>%(title)s</a>") % {
                    "href": next_exercise["path"],
                    "title": _(next_exercise["title"]),
                })

        # Return no message in release mode; "data saved" message in debug mode.
        return JsonResponse({})

    if request.method == "GET":
        """
        Given an exercise_id, retrieve an exercise log for this user.
        """
        user = request.session["facility_user"]
        log = get_object_or_None(ExerciseLog, user=user, exercise_id=exercise_id) or ExerciseLog()
        return JsonResponse(log)


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
@student_log_api(logged_out_message=ugettext_lazy("Attempt logs not active."))
def attempt_log(request, exercise_id):
    """
    RESTful API endpoint for AttemptLogs.
    """

    if request.method == "POST":

        form = AttemptLogForm(data=json.loads(request.raw_post_data))
        if not form.is_valid():
            raise Exception(form.errors)
        data = form.data

        # More robust extraction of previous object
        user = request.session["facility_user"]

        try:
            AttemptLog.objects.create(
                user=user,
                exercise_id=data["exercise_id"],
                random_seed=data["random_seed"],
                answer_given=data["answer_given"],
                points_awarded=data["points"],
                correct=data["correct"],
                context_type=data["context_type"],
                language=data.get("language") or request.language,
                )
        except ValidationError as e:
            return JsonResponseMessageError(_("Could not save AttemptLog") + u": %s" % e)

        # Return no message in release mode; "data saved" message in debug mode.
        return JsonResponse({})

    if request.method == "GET":
        """
        Given an exercise_id, retrieve a list of the last ten attempt logs for this user.
        """
        user = request.session["facility_user"]
        logs = AttemptLog.objects \
                .filter(user=user, exercise_id=exercise_id, context_type="exercise") \
                .order_by("-timestamp") \
                .values("exercise_id", "correct", "context_type", "timestamp", "time_taken", "answer_given", "points_awarded")[:10]
        return JsonResponse(list(reversed(logs)))



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

UNIT_EXERCISES = {}

@dynamic_settings
@api_handle_error_with_json
@backend_cache_page
def exercise(request, exercise_id):
    exercise = get_exercise_data(request, exercise_id)
    if "facility_user" in request.session:
        facility_id = request.session["facility_user"].facility.id
        current_unit = get_current_unit_settings_value(facility_id)
        student_grade = ds["ab_testing"].student_grade_level
        if student_grade:
            if not UNIT_EXERCISES.has_key(current_unit):
                for playlist in Playlist.all():
                    if not UNIT_EXERCISES.has_key(playlist.unit):
                        UNIT_EXERCISES[playlist.unit] = {}
                    # Assumes gx_pyy id for playlist.
                    grade = int(playlist.id[1])
                    if not UNIT_EXERCISES[playlist.unit].has_key(grade):
                        UNIT_EXERCISES[playlist.unit][grade] = []
                    for entry in playlist.entries:
                        if entry["entity_kind"] == "Exercise":
                            UNIT_EXERCISES[playlist.unit][grade].append(entry["entity_id"])

            current_unit_exercises = UNIT_EXERCISES.get(current_unit, {}).get(student_grade, [])

            if ds["distributed"].turn_off_points_for_exercises:
                exercise["basepoints"] = 0
            elif ds["distributed"].turn_off_points_for_noncurrent_unit and exercise["exercise_id"] not in current_unit_exercises:
                exercise["basepoints"] = 0
            else:
                # TODO-BLOCKER(rtibbles): Revisit this, pending determination of quiz in every playlist.
                exercise["basepoints"] = settings.UNIT_POINTS / (
                    len(current_unit_exercises)*(ds["distributed"].streak_correct_needed +
                        ds["distributed"].fixed_block_exercises +
                        ds["distributed"].quiz_repeats))
    if exercise:
        return JsonResponse(exercise)
    else:
        return JsonResponseMessageError("Exercise with id %(exercise_id)s not found" % {"exercise_id": exercise_id}, status=404)


@api_handle_error_with_json
@backend_cache_page
def video(request, video_id):
    video = get_video_data(request, video_id)
    if video:
        return JsonResponse(video)
    else:
        return JsonResponseMessageError("Video with id %(video_id)s not found" % {"video_id": video_id}, status=404)


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
