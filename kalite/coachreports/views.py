import re
from annoying.decorators import render_to
from ast import literal_eval
from collections_local_copy import OrderedDict
from math import sqrt

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.contrib.messages import ERROR
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.utils.translation import ungettext, ugettext_lazy, ugettext as _

from .api_views import get_data_form, stats_dict
from django.shortcuts import get_object_or_404

from kalite.distributed.api_views import compute_total_points
from kalite.facility.decorators import facility_required
from kalite.facility.models import Facility, FacilityUser, FacilityGroup
from kalite.i18n import lcode_to_django_lang
from kalite.main.models import AttemptLog, VideoLog, ExerciseLog, UserLog
from kalite.playlist.models import VanillaPlaylist as Playlist
from kalite.shared.decorators import require_authorized_access_to_student_data, require_authorized_admin, get_user_from_request
from kalite.store.models import StoreItem, StoreTransactionLog
from kalite.student_testing.api_resources import TestResource
from kalite.student_testing.models import TestLog
from kalite.topic_tools import get_topic_exercises, get_topic_videos, get_knowledgemap_topics, get_exercise_cache, get_node_cache

# shared by test_view and test_detail view
SUMMARY_STATS = [ugettext_lazy('Max'), ugettext_lazy('Min'), ugettext_lazy('Average'), ugettext_lazy('Std Dev')]


def get_accessible_objects_from_logged_in_user(request, facility):
    """Given a request, get all the facility/group/user objects relevant to the request,
    subject to the permissions of the user type.

    Make sure the returned `facilities` object is always a Facility queryset or an empty list.
    """

    # Options to select.  Note that this depends on the user.
    facilities = []
    if request.user.is_superuser:
        facilities = Facility.objects.all()
        # Groups is now a list of objects with a key for facility id, and a key
        # for the list of groups at that facility.
        # TODO: Make this more efficient.
        groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]

    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        if user.is_teacher:
            facilities = Facility.objects.all()
            groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]
        else:
            # Students can only access their group
            if facility and isinstance(facility, Facility):
                facilities = Facility.objects.filter(id=facility.id)
            if not user.group:
                groups = []
            else:
                groups = [{"facility": user.facility.id,
                           "groups": FacilityGroup.objects.filter(id=request.session["facility_user"].group)}]
    elif facility:
        facilities = Facility.objects.filter(id=facility.id)
        groups = [{"facility": facility.id, "groups": FacilityGroup.objects.filter(facility=facility)}]
    else:
        # defaults to all facilities and groups
        facilities = Facility.objects.all()
        groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]

    ungrouped_available = False
    for f in facilities:
        # Check if there is at least one facility with ungrouped students.
        ungrouped_available = f.has_ungrouped_students
        if ungrouped_available:
            break

    return (groups, facilities, ungrouped_available)


def plotting_metadata_context(request, facility=None, topic_path=[], *args, **kwargs):
    """Basic context for any plot: get the data form, a dictionary of stat definitions,
    and the full gamut of facility/group objects relevant to the request."""

    # Get the form, and retrieve the API data
    form = get_data_form(request, facility=facility, topic_path=topic_path, *args, **kwargs)

    (groups, facilities, ungrouped_available) = get_accessible_objects_from_logged_in_user(request, facility=facility)

    return {
        "form": form.data,
        "stats": stats_dict,
        "groups": groups,
        "facilities": facilities,
        "ungrouped_available": ungrouped_available,
    }


def coach_nav_context(request, report_id):
    """
    Updates the context of all coach reports with the facility, group, and report to have selected
    by default on page load
    """
    facility_id = request.GET.get("facility_id", None)
    facility = None
    if facility_id:
        facility = Facility.objects.get(id=facility_id)
    group_id = request.GET.get("group_id", "")
    context = {
        "nav_state": {
            "facility_id": facility_id,
            "group_id": group_id,
            "report_id": report_id,
        }
    }
    return (facility, group_id, context)


@require_authorized_admin
@render_to("coachreports/timeline_view.html")
def timeline_view(request, xaxis="", yaxis=""):
    """timeline view (line plot, xaxis is time-related): just send metadata; data will be requested via AJAX"""
    facility, group_id, context = coach_nav_context(request, "timeline")
    context.update(plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis))
    context["title"] = _("Timeline plot")
    try:
        context["title"] = _(u"%(yaxis_name)s over time") % {
            "yaxis_name": [stat["name"] for stat in stats_dict if stat["key"] == yaxis][0],
        }
    except:
        pass

    return context


@require_authorized_admin
@render_to("coachreports/scatter_view.html")
def scatter_view(request, xaxis="", yaxis=""):
    """Scatter view (scatter plot): just send metadata; data will be requested via AJAX"""
    xaxis = "pct_mastery"
    yaxis = "effort"
    facility, group_id, context = coach_nav_context(request, "scatter")
    context.update(plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis))
    context["title"] = _("Scatter plot")
    try:
        context["title"] = _(u"%(yaxis_name)s versus %(xaxis_name)s") % {
            "xaxis_name": [stat["name"] for stat in stats_dict if stat["key"] == xaxis][0],
            "yaxis_name": [stat["name"] for stat in stats_dict if stat["key"] == yaxis][0],
        }
    except:
        pass
    return context


@require_authorized_access_to_student_data
@render_to("coachreports/student_view.html")
def student_view(request):
    """
    Student view: data generated on the back-end.

    Student view lists a by-topic-summary of their activity logs.
    """
    return student_view_context(request=request)


@require_authorized_access_to_student_data
def student_view_context(request):
    """
    Context done separately, to be importable for similar pages.
    """
    user = get_user_from_request(request=request)
    if not user:
        raise Http404("User not found.")

    context = {
        "facility_id": user.facility.id,
        "student": user,
    }
    return context


@require_authorized_admin
@facility_required
@render_to("coachreports/landing_page.html")
def landing_page(request, facility):
    """Landing page needs plotting context in order to generate the navbar"""
    return plotting_metadata_context(request, facility=facility)


@require_authorized_admin
@render_to("coachreports/tabular_view.html")
def tabular_view(request, report_type="exercise"):
    """Tabular view also gets data server-side."""
    # important for setting the defaults for the coach nav bar

    language = lcode_to_django_lang(request.language)

    facility, group_id, context = coach_nav_context(request, "tabular")

    # Define how students are ordered--used to be as efficient as possible.
    student_ordering = ["last_name", "first_name", "username"]

    # Get a list of topics (sorted) and groups
    topics = [get_node_cache("Topic", language=language).get(tid["id"]) for tid in get_knowledgemap_topics(language=language) if report_type.title() in tid["contains"]]
    playlists = Playlist.all()

    (groups, facilities, ungrouped_available) = get_accessible_objects_from_logged_in_user(request, facility=facility)

    context.update(plotting_metadata_context(request, facility=facility))

    context.update({
        # For translators: the following two translations are nouns
        "report_types": ({"value": "exercise", "name":_("exercise")}, {"value": "video", "name": _("video")}),
        "request_report_type": report_type,
        "topics": [{"id": t["id"], "title": t["title"]} for t in topics if t],
        "playlists": [{"id": p.id, "title": p.title, "tag": p.tag} for p in playlists if p],
    })

    # get querystring info
    topic_id = request.GET.get("topic", "")
    playlist_id = request.GET.get("playlist", "")
    # No valid data; just show generic
    # Exactly one of topic_id or playlist_id should be present
    if not ((topic_id or playlist_id) and not (topic_id and playlist_id)):
        if playlists:
            messages.add_message(request, ERROR, _("Please select a playlist."))
        elif topics:
            messages.add_message(request, ERROR, _("Please select a topic."))
        return context

    playlist = (filter(lambda p: p.id == playlist_id, Playlist.all()) or [None])[0]

    if group_id:
        # Narrow by group
        from control_panel.api_resources import UNGROUPED_KEY
        if group_id == UNGROUPED_KEY:
            users = FacilityUser.objects.filter(group__isnull=True, is_teacher=False)
            if facility:
                # filter only those ungrouped students for the facility
                users = users.filter(facility=facility)
                users = users.order_by(*student_ordering)
            else:
                # filter all ungroup students
                users = FacilityUser.objects.filter(group__isnull=True, is_teacher=False).order_by(*student_ordering)

        else:
            users = FacilityUser.objects.filter(
                group=group_id, is_teacher=False).order_by(*student_ordering)

    elif facility:
        # Narrow by facility
        search_groups = [groups_dict["groups"] for groups_dict in groups if groups_dict["facility"] == facility.id]
        assert len(search_groups) <= 1, "Should only have one or zero matches."

        # Return groups and ungrouped
        search_groups = search_groups[0]  # make sure to include ungrouped students
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None, facility=facility), is_teacher=False).order_by(*student_ordering)

    else:
        # Show all (including ungrouped)
        search_groups = []
        for groups_dict in groups:
            search_groups += groups_dict["groups"]
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None), is_teacher=False).order_by(*student_ordering)

    # We have enough data to render over a group of students
    # Get type-specific information
    if report_type == "exercise":
        # Fill in exercises
        if topic_id:
            exercises = get_topic_exercises(topic_id=topic_id)
        elif playlist:
            exercises = playlist.get_playlist_entries("Exercise", language=language)

        context["exercises"] = exercises

        # More code, but much faster
        exercise_names = [ex["id"] for ex in context["exercises"]]
        # Get students
        context["students"] = []
        exlogs = ExerciseLog.objects \
            .filter(user__in=users, exercise_id__in=exercise_names) \
            .order_by(*["user__%s" % field for field in student_ordering]) \
            .values("user__id", "struggling", "complete", "exercise_id")
        exlogs = list(exlogs)  # force the query to be evaluated

        exlog_idx = 0
        for user in users:
            log_table = {}
            while exlog_idx < len(exlogs) and exlogs[exlog_idx]["user__id"] == user.id:
                log_table[exlogs[exlog_idx]["exercise_id"]] = exlogs[exlog_idx]
                exlog_idx += 1

            context["students"].append({  # this could be DRYer
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "name": user.get_name(),
                "id": user.id,
                "exercise_logs": log_table,
            })

    elif report_type == "video":
        # Fill in videos
        if topic_id:
            context["videos"] = get_topic_videos(topic_id=topic_id)
        elif playlist:
            context["videos"] = playlist.get_playlist_entries("Video", language=language)

        # More code, but much faster
        video_ids = [vid["id"] for vid in context["videos"]]
        # Get students
        context["students"] = []
        vidlogs = VideoLog.objects \
            .filter(user__in=users, video_id__in=video_ids) \
            .order_by(*["user__%s" % field for field in student_ordering])\
            .values("user__id", "complete", "video_id", "total_seconds_watched", "points")
        vidlogs = list(vidlogs)  # force the query to be executed now

        vidlog_idx = 0
        for user in users:
            log_table = {}
            while vidlog_idx < len(vidlogs) and vidlogs[vidlog_idx]["user__id"] == user.id:
                log_table[vidlogs[vidlog_idx]["video_id"]] = vidlogs[vidlog_idx]
                vidlog_idx += 1

            context["students"].append({  # this could be DRYer
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "name": user.get_name(),
                "id": user.id,
                "video_logs": log_table,
            })
    else:
        raise Http404(_("Unknown report_type: %(report_type)s") % {"report_type": report_type})

    # Validate results by showing user messages.
    if not users:
        # 1. check group facility groups
        if len(groups) > 0 and not groups[0]['groups']:
            # 1. No groups available (for facility) and "no students" returned.
            messages.add_message(request, ERROR,
                                 _("No learner accounts have been created for selected facility/group."))
        elif topic_id and playlist_id:
            # 2. Both topic and playlist are selected.
            messages.add_message(request, ERROR, _("Please select either a topic or a playlist above, but not both."))
        elif not topic_id and not playlist_id:
            # 3. Group was selected, but data not queried because a topic or playlist was not selected.
            if playlists:
                # 4. No playlist was selected.
                messages.add_message(request, ERROR, _("Please select a playlist."))
            elif topics:
                # 5. No topic was selected.
                messages.add_message(request, ERROR, _("Please select a topic."))
        else:
            # 6. Everything specified, but no users fit the query.
            messages.add_message(request, ERROR, _("No learner accounts in this group have been created."))
    # End: Validate results by showing user messages.

    log_coach_report_view(request)

    return context


@require_authorized_admin
@render_to("coachreports/test_view.html")
def test_view(request):
    """Test view gets data server-side and displays exam results"""
    facility, group_id, context = coach_nav_context(request, "test")
    # Get students
    users = get_user_queryset(request, facility, group_id)

    # Get the TestLog objects generated by this group of students
    # TODO(cpauya): what about queryset for ungrouped students?
    test_logs = None
    from control_panel.api_resources import UNGROUPED_KEY
    if group_id:
        test_logs = TestLog.objects.filter(user__group=group_id)
        # Narrow all by ungroup facility user
        if group_id == UNGROUPED_KEY:
            test_logs = TestLog.objects.filter(user__group__isnull=True)
            if facility:
                TestLog.objects.filter(user__facility=facility, user__group__isnull=True)
            else:
                TestLog.objects.filter(user__group__isnull=True)

    elif facility:
        test_logs = TestLog.objects.filter(user__facility=facility)

    else:
        # filter by all facilities and groups for the user
        (groups, facilities, ungrouped_available) = get_accessible_objects_from_logged_in_user(request, facility=facility)
        if facilities:
            facility_ids = facilities.values_list("id", flat=True)
            test_logs = TestLog.objects.filter(user__facility__id__in=facility_ids)

    # Get list of all test objects
    test_resource = TestResource()
    tests_list = test_resource._read_tests()

    # Get completed test objects (used as columns)
    completed_test_ids = set([item.test for item in test_logs])
    test_objects = [test for test in tests_list if test.test_id in completed_test_ids]

    # Create the table
    results_table = OrderedDict()
    for s in users:
        s.name = s.get_name()
        user_test_logs = [log for log in test_logs if log.user == s]
        results_table[s] = []
        for t in test_objects:
            log_object = next((log for log in user_test_logs if log.test == t.test_id), '')
            # The template expects a status and a score to display
            if log_object:
                test_object = log_object.get_test_object()
                score = round(100 * float(log_object.total_correct) / float(test_object.total_questions), 1)
                display_score = "%(score)d%% (%(correct)d/%(total_questions)d)" % {'score': score, 'correct': log_object.total_correct, 'total_questions': test_object.total_questions}
                if log_object.complete:
                    # Case: completed => we show % score
                    if score >= 80:
                        status = _("pass")
                    elif score >= 60:
                        status = _("borderline")
                    else:
                        status = _("fail" )
                    results_table[s].append({
                        "status": status,
                        "cell_display": display_score,
                        "title": status.title(),
                    })
                else:
                    # Case: has started, but has not finished => we display % score & # remaining in title
                    n_remaining = test_object.total_questions - log_object.index
                    status = _("incomplete")
                    results_table[s].append({
                        "status": status,
                        "cell_display": display_score,
                        "title": status.title() + ": " + ungettext("%(n_remaining)d problem remaining",
                                                                   n_remaining) % {'n_remaining': n_remaining},
                    })
            else:
                # Case: has not started
                status = _("not started")
                results_table[s].append({
                    "status": status,
                    "cell_display": "",
                    "title": status.title(),
                })

        # This retrieves stats for students
        score_list = [round(100 * float(result.total_correct) / float(result.get_test_object().total_questions), 1) for result in user_test_logs]
        for stat in SUMMARY_STATS:
            if score_list:
                results_table[s].append({
                    "status": "statistic",
                    "cell_display": "%d%%" % return_list_stat(score_list, stat),
                })
            else:
                results_table[s].append({
                    "status": "statistic",
                    "cell_display": "",
                })

    # This retrieves stats for tests
    stats_dict = OrderedDict()
    for stat in SUMMARY_STATS:
        stats_dict[stat] = []
        for test_obj in test_objects:
            # get the logs for this test across all users and then add summary stats
            log_scores = [round(100 * float(test_log.total_correct) / float(test_log.get_test_object().total_questions), 1) for test_log in test_logs if test_log.test == test_obj.test_id]
            stats_dict[stat].append("%d%%" % return_list_stat(log_scores, stat))

    context.update(plotting_metadata_context(request, facility=facility))
    context.update({
        "results_table": results_table,
        "test_columns": test_objects,
        "summary_stats": SUMMARY_STATS,
        "stats_dict": stats_dict,
    })

    return context


@require_authorized_admin
@render_to("coachreports/test_detail_view.html")
def test_detail_view(request, test_id):
    """View details of student performance on specific exams"""

    facility, group_id, context = coach_nav_context(request, "test")
    # get users in this facility and group
    users = get_user_queryset(request, facility, group_id)

    # Get test object
    test_resource = TestResource()
    test_obj = test_resource._read_test(test_id=test_id)

    # get all of the test logs for this specific test object and generated by these specific users
    if group_id:
        from control_panel.api_resources import UNGROUPED_KEY
        test_logs = TestLog.objects.filter(user__group=group_id, test=test_id)

        # Narrow all by ungroup facility user
        if group_id == UNGROUPED_KEY:
            if facility:
                test_logs = TestLog.objects.filter(user__group__isnull=True)
            else:
                test_logs = TestLog.objects.filter(facility=facility, user__group__isnull=True)
    else:
        # covers the all groups case
        test_logs = TestLog.objects.filter(user__facility=facility, test=test_id)

    results_table, scores_dict = OrderedDict(), OrderedDict()
    # build this up now to use in summary stats section
    ex_ids = set(literal_eval(test_obj.ids))
    for ex in ex_ids:
        scores_dict[ex] = []
    for s in users:
        s.name = s.get_name()
        user_attempts = AttemptLog.objects.filter(user=s, context_type='test', context_id=test_id)
        results_table[s] = []
        attempts_count_total, attempts_count_correct_total = 0, 0
        for ex in ex_ids:
            attempts = [attempt for attempt in user_attempts if attempt.exercise_id == ex]

            attempts_count = len(attempts)
            attempts_count_correct = len([attempt for attempt in attempts if attempt.correct])

            attempts_count_total += attempts_count
            attempts_count_correct_total += attempts_count_correct

            if attempts_count:
                score = round(100 * float(attempts_count_correct)/float(attempts_count), 1)
                scores_dict[ex].append(score)
                display_score = "%d%%" % score
            else:
                score = ''
                display_score = ''

            results_table[s].append({
                'display_score': display_score,
                'raw_score': score,
            })

        # Calc overall score
        if attempts_count_total:
            score = round(100 * float(attempts_count_correct_total)/float(attempts_count_total), 1)
            display_score = "%d%%" % score
            fraction_correct = "(%(correct)d/%(attempts)d)" % ({'correct': attempts_count_correct_total, 'attempts': attempts_count_total})
        else:
            score = ''
            display_score = ''
            fraction_correct = ''

        results_table[s].append({
            'display_score': display_score,
            'raw_score': score,
            'title': fraction_correct,
        })

    # This retrieves stats for individual exercises
    stats_dict = OrderedDict()
    for stat in SUMMARY_STATS:
        stats_dict[stat] = []
        for ex in ex_ids:
            scores_list = scores_dict[ex]
            if scores_list:
                stats_dict[stat].append("%d%%" % return_list_stat(scores_list, stat))
            else:
                stats_dict[stat].append('')

    # replace the exercise ids with their full names
    exercises = get_exercise_cache()
    ex_titles = []
    for ex in ex_ids:
        ex_titles.append(exercises[ex]['title'])

    # provide a list of test options to view for this group/facility combo
    if group_id:
        test_logs = TestLog.objects.filter(user__group=group_id)
    else:
        # covers the all/no groups case
        test_logs = TestLog.objects.filter(user__facility=facility)
    test_objects = test_resource._read_tests()
    unique_test_ids = set([test_log.test for test_log in test_logs])
    test_options = [{'id': obj.test_id, 'url': reverse('test_detail_view', kwargs={'test_id':obj.test_id}), 'title': obj.title} for obj in test_objects if obj.test_id in unique_test_ids]
    context = plotting_metadata_context(request, facility=facility)
    context.update({
        "test_obj": test_obj,
        "ex_cols": ex_titles,
        "results_table": results_table,
        "stats_dict": stats_dict,
        "test_options": test_options,
    })
    return context


@require_authorized_admin
@facility_required
@render_to("coachreports/spending_report_view.html")
def spending_report_view(request, facility):
    """View total points remaining for students"""
    group_id = request.GET.get("group", "")
    users = get_user_queryset(request, facility, group_id)
    user_points = {}
    for user in users:
        user_points[user] = compute_total_points(user)
    context = plotting_metadata_context(request, facility=facility)
    context.update({
        "user_points": user_points,
    })
    return context


@require_authorized_admin
@render_to("coachreports/spending_report_detail_view.html")
def spending_report_detail_view(request, user_id):
    """View transaction logs for student"""
    student = get_object_or_404(FacilityUser, id=user_id)
    transactions = StoreTransactionLog.objects.filter(user=student, context_type='unit').order_by('purchased_at') # TODO(dylanjbarth): filter out gift cards?
    context = plotting_metadata_context(request)
    store_items = StoreItem.all()
    humanized_transactions = []
    for t in transactions:
        # Hydrate the store item object
        item_key = t.item.strip("/").split("/")[-1]
        humanized_transactions.append({
            "purchased_at": t.purchased_at,
            "item": store_items.get(item_key, ""),
            "value": abs(t.value),
            "context_id": t.context_id,
        })
    context.update({
        "student": student,
        "transactions": humanized_transactions,
    })
    return context


def get_user_queryset(request, facility, group_id):
    """Return set of users appropriate to the facility and group"""
    student_ordering = ["last_name", "first_name", "username"]
    (groups, facilities, ungrouped_available) = get_accessible_objects_from_logged_in_user(request, facility=facility)
    from control_panel.api_resources import UNGROUPED_KEY
    if group_id:
        # Narrow by group
        users = FacilityUser.objects.filter(
            group=group_id, is_teacher=False).order_by(*student_ordering)
        # Narrow all by ungroup user
        if group_id == UNGROUPED_KEY:
            users = FacilityUser.objects.filter(group__isnull=True, is_teacher=False).order_by(*student_ordering)
            if facility:
                users = FacilityUser.objects.filter(facility=facility, group__isnull=True,
                                                    is_teacher=False).order_by(*student_ordering)

    elif facility:
        # Narrow by facility
        search_groups = [groups_dict["groups"] for groups_dict in groups if groups_dict["facility"] == facility.id]
        assert len(search_groups) <= 1, "Should only have one or zero matches."

        # Return groups and ungrouped
        search_groups = search_groups[0]  # make sure to include ungrouped students
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None, facility=facility), is_teacher=False).order_by(*student_ordering)

    else:
        # Show all (including ungrouped)
        search_groups = []
        for groups_dict in groups:
            search_groups += groups_dict["groups"]
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None), is_teacher=False).order_by(*student_ordering)

    return users


def log_coach_report_view(request):
    """Record coach report view by teacher"""
    if "facility_user" in request.session:
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.error("Failed to update Teacher userlog activity login: %s" % e)


def return_list_stat(stat_list, stat):
    """
    Return the stat requests from the list provided.
    Ex: given stat_list = [1, 2, 3] and stat = 'Max' return 3
    """
    if stat == 'Max':
        return_stat = max(stat_list)
    elif stat == 'Min':
        return_stat = min(stat_list)
    elif stat == 'Average':
        return_stat = sum(stat_list)/len(stat_list)
    elif stat == 'Std Dev':
        avg_score = sum(stat_list)/len(stat_list)
        variance = map(lambda x: (x - avg_score)**2, stat_list)
        avg_variance = sum(variance)/len(variance)
        return_stat = sqrt(avg_variance)

    return round(return_stat, 1)
