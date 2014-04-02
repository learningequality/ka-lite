"""
"""
import datetime
import os
from annoying.decorators import render_to, wraps
from annoying.functions import get_object_or_None
from collections_local_copy import OrderedDict, namedtuple

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Sum, Max
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from .forms import ZoneForm, UploadFileForm, DateRangeForm
from fle_utils.internet import CsvResponse, render_to_csv
from fle_utils.django_utils.paginate import paginate_users, pages_to_show
from kalite.coachreports.views import student_view_context
from kalite.facility.decorators import facility_required
from kalite.facility.forms import FacilityForm
from kalite.facility.models import Facility, FacilityUser, FacilityGroup
from kalite.main.models import ExerciseLog, VideoLog, UserLog, UserLogSummary
from kalite.main.topic_tools import get_node_cache
from kalite.shared.decorators import require_authorized_admin, require_authorized_access_to_student_data
from kalite.version import VERSION, VERSION_INFO
from securesync.models import DeviceZone, Device, Zone, SyncSession


def set_clock_context(request):
    return {
        "clock_set": getattr(settings, "ENABLE_CLOCK_SET", False),
    }

def sync_now_context(request):
    return {
        "in_a_zone":  Device.get_own_device().get_zone() is not None,
    }


@require_authorized_admin
@render_to("control_panel/zone_form.html")
def zone_form(request, zone_id):
    context = process_zone_form
    if request.method == "POST" and context["form"].is_valid:
        return HttpResponseRedirect(reverse("zone_management", kwargs={ "zone_id": zone_id }))
    else:
        return context

def process_zone_form(request, zone_id):
    context = control_panel_context(request, zone_id=zone_id)

    if request.method != "POST":
        form = ZoneForm(instance=context["zone"])

    else:  # POST request
        form = ZoneForm(data=request.POST, instance=context["zone"])

        if not form.is_valid():
            messages.error(request, _("Failed to save the sharing network; please review errors below."))

        else:
            form.instance.save()
            if zone_id == "new":
                zone_id = form.instance.pk
            return HttpResponseRedirect(reverse("zone_management", kwargs={ "zone_id": zone_id }))

    context.update({"form": form})
    return context


@require_authorized_admin
@render_to("control_panel/zone_management.html")
def zone_management(request, zone_id="None"):
    context = control_panel_context(request, zone_id=zone_id)
    own_device = Device.get_own_device()

    if not context["zone"] and (zone_id != "None" or Zone.objects.count() != 0 or settings.CENTRAL_SERVER):
        raise Http404()  # on distributed server, we can make due if they're not registered.

    # Accumulate device data
    device_data = OrderedDict()
    if context["zone"]:
        devices = Device.objects.filter(devicezone__zone=context["zone"])
    else:
        devices = Device.objects.filter(devicemetadata__is_trusted=False)

    for device in list(devices.order_by("devicemetadata__is_demo_device", "name")):

        user_activity = UserLogSummary.objects.filter(device=device)
        sync_sessions = SyncSession.objects.filter(client_device=device)
        if not settings.CENTRAL_SERVER and device.id != own_device.id:  # Non-local sync sessions unavailable on distributed server
            sync_sessions = None

        exercise_activity = ExerciseLog.objects.filter(signed_by=device)

        device_data[device.id] = {
            "name": device.name or device.id,
            "num_times_synced": sync_sessions.count() if sync_sessions is not None else None,
            "last_time_synced": sync_sessions.aggregate(Max("timestamp"))["timestamp__max"] if sync_sessions is not None else None,
            "is_demo_device": device.get_metadata().is_demo_device,
            "is_own_device": device.get_metadata().is_own_device and not settings.CENTRAL_SERVER,
            "last_time_used":   exercise_activity.order_by("-completion_timestamp")[0:1] if user_activity.count() == 0 else user_activity.order_by("-last_activity_datetime", "-end_datetime")[0],
            "counter": device.get_counter_position(),
            "is_registered": device.is_registered(),
        }

    # Accumulate facility data
    facility_data = OrderedDict()
    if context["zone"]:
        facilities = Facility.objects.by_zone(context["zone"])
    else:
        facilities = Facility.objects.all()
    for facility in list(facilities.order_by("name")):

        user_activity = UserLogSummary.objects.filter(user__facility=facility)
        exercise_activity = ExerciseLog.objects.filter(user__facility=facility)

        facility_data[facility.id] = {
            "name": facility.name,
            "num_users":  FacilityUser.objects.filter(facility=facility).count(),
            "num_groups": FacilityGroup.objects.filter(facility=facility).count(),
            "id": facility.id,
            "last_time_used":   exercise_activity.order_by("-completion_timestamp")[0:1] if user_activity.count() == 0 else user_activity.order_by("-last_activity_datetime", "-end_datetime")[0],
            "is_deletable": facility.is_deletable(),
        }

    context.update({
        "facilities": facility_data,
        "devices": device_data,
        "upload_form": UploadFileForm(),
        "own_device_is_trusted": Device.get_own_device().get_metadata().is_trusted,
    })
    context.update(set_clock_context(request))
    return context


@require_authorized_admin
def delete_zone(request, zone_id):
    zone = get_object_or_404(Zone, id=zone_id)
    if not zone.has_dependencies(passable_classes=["Organization"]):
        zone.delete()
        messages.success(request, _("You have successfully deleted ") + zone.name + ".")
    else:
        messages.warning(request, _("You cannot delete this zone because it is syncing data with with %d device(s)") % zone.devicezone_set.count())
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
@render_to("control_panel/device_management.html")
def device_management(request, device_id, zone_id=None, n_sessions=10):
    context = control_panel_context(request, zone_id=zone_id, device_id=device_id)

    # Retrieve sync sessions
    all_sessions = SyncSession.objects.filter(client_device=context["device"])
    total_sessions = all_sessions.count()
    shown_sessions = list(all_sessions.order_by("-timestamp")[:n_sessions])

    context.update({
        "shown_sessions": shown_sessions,
        "total_sessions": total_sessions,
        "is_own_device": not settings.CENTRAL_SERVER and device_id == Device.get_own_device().id,
    })

    # If local (and, for security purposes, a distributed server), get device metadata
    if context["is_own_device"]:
        context.update(local_device_context(request))

    return context


@facility_required
@require_authorized_admin
@render_to("control_panel/facility_form.html")
def facility_form(request, facility, zone_id=None):
    context = control_panel_context(request, zone_id=zone_id, facility_id=facility.id)

    if request.method != "POST":
        form = FacilityForm(instance=context["facility"])

    else:
        form = FacilityForm(data=request.POST, instance=context["facility"])
        if not form.is_valid():
            messages.error(request, _("Failed to save the facility; please review errors below."))
        else:
            form.instance.zone_fallback = get_object_or_404(Zone, pk=zone_id)
            form.save()
            return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": zone_id}))

    context.update({"form": form})
    return context


@facility_required
@require_authorized_admin
@render_to("control_panel/group_report.html")
def group_report(request, facility, group_id=None, zone_id=None):
    context = group_report_context(
        facility_id=facility.id,
        group_id=group_id or request.REQUEST.get("group", ""),
        topic_id=request.REQUEST.get("topic", ""),
        zone_id=zone_id
    )

    context.update(control_panel_context(request, zone_id=zone_id, facility_id=facility.id, group_id=group_id))
    return context


@facility_required
@require_authorized_admin
@render_to("control_panel/facility_management.html")
@render_to_csv(["students", "teachers"], key_label="user_id", order="stacked")
def facility_management(request, facility, group_id=None, zone_id=None, frequency=None, period_start="", period_end="", user_type=None, per_page=25):
    context = control_panel_context(request, zone_id=zone_id, facility_id=facility.id)

    #Get pagination details
    coach_page = request.REQUEST.get("coaches_page", "1")
    coach_per_page = request.REQUEST.get("coaches_per_page", "5")
    student_page = request.REQUEST.get("students_page", "1")
    student_per_page = request.REQUEST.get("students_per_page", "25" if group_id else "10")

    # This could be moved into a function shared across files, if necessary.
    #   For now, moving into function, as outside if function it looks more
    #   general-purpose than it's being used / tested now.

    def get_users_from_group(user_type, group_id, facility=None):
        if user_type == "coaches":
            user_list = FacilityUser.objects \
                .filter(is_teacher=True) \
                .filter(facility=facility)
        elif _(group_id) == _("Ungrouped"):
            user_list = FacilityUser.objects \
                .filter(is_teacher=False) \
                .filter(facility=facility, group__isnull=True)
        elif group_id:
            user_list = FacilityUser.objects \
                .filter(facility=facility, group=group_id, is_teacher=False)
        else:
            user_list = FacilityUser.objects \
                .filter(facility=facility, is_teacher=False)

        user_list = user_list \
            .order_by("last_name", "first_name", "username") \
            .prefetch_related("group")

        return user_list


    # Basic data
    groups = FacilityGroup.objects.filter(facility=context["facility"]).order_by("name")
    group = group_id and get_object_or_None(FacilityGroup, id=group_id)
    coaches = get_users_from_group(user_type="coaches", group_id=group_id, facility=facility)
    students = get_users_from_group(user_type="students", group_id=group_id, facility=facility)

    if request.method != "POST":
        form = DateRangeForm()

    else:  # POST request
        form = DateRangeForm(data=request.POST)

        if not form.is_valid():
            messages.error(request, _("Unexpected error parsing date range; please review and re-submit."))
            period_start = None
            period_end = None
        else:
            frequency = frequency or request.GET.get("frequency", "months")
            period_start = period_start or form.data["period_start"]
            period_end = period_end or form.data["period_end"]
            (period_start, period_end) = _get_date_range(frequency, period_start, period_end)

    (student_data, group_data) = _get_user_usage_data(students, groups, period_start=period_start, period_end=period_end, group_id=group_id)
    (coach_data, coach_group_data) = _get_user_usage_data(coaches, period_start=period_start, period_end=period_end, group_id=group_id)

    coach_data, coach_urls = paginate_users(request, coach_data, "coaches", page=coach_page, per_page=coach_per_page)
    student_data, student_urls = paginate_users(request, student_data, "students", page=student_page, per_page=student_per_page)

    page_urls = {
        "coaches": coach_urls,
        "students": student_urls,
    }

    context.update({
        "form": form,
        "group": group,
        "date_range": [period_start, period_end],
        "group_id": group_id,
        "page_urls": page_urls,
        "groups": group_data,
        "students": student_data,
        "coaches": coach_data,
    })
    return context


@require_authorized_access_to_student_data
@render_to("control_panel/account_management.html")
def account_management(request):

    # Only log 'coachreport' activity for students,
    #   (otherwise it's hard to compare teachers)
    if "facility_user" in request.session and not request.session["facility_user"].is_teacher and reverse("login") not in request.META.get("HTTP_REFERER", ""):
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.error("Failed to update student userlog activity: %s" % e)

    return student_view_context(request)


# data functions

def _get_date_range(frequency, period_start, period_end):
    """
    Hack function (while CSV is in initial stages),
        returns dates of beginning and end of last month.
    Should be extended to do something more generic, based on
    "frequency", and moved into utils/general.py
    """

    assert frequency == "months"

    if frequency == "months":  # only works for months ATM
        if not (period_start or period_end):
            cur_date = datetime.datetime.now()
            first_this_month = datetime.datetime(year=cur_date.year, month=cur_date.month, day=1, hour=0, minute=0, second=0)
            period_end = first_this_month - datetime.timedelta(seconds=1)
            period_start = datetime.datetime(year=period_end.year, month=period_end.month, day=1)
        else:
            period_end = period_end or period_start + datetime.timedelta(days=30)
            period_start = period_start or period_end - datetime.timedelta(days=30)
    return (period_start, period_end)


def _get_user_usage_data(users, groups=None, period_start=None, period_end=None, group_id=None):
    """
    Returns facility user data, within the given date range.
    """

    groups = groups or set([user.group for user in users])

    # compute period start and end
    # Now compute stats, based on queried data
    num_exercises = len(get_node_cache('Exercise'))
    user_data = OrderedDict()
    group_data = OrderedDict()


    # Make queries efficiently
    exercise_logs = ExerciseLog.objects.filter(user__in=users, complete=True)
    video_logs = VideoLog.objects.filter(user__in=users)
    login_logs = UserLogSummary.objects.filter(user__in=users)

    # filter results
    if period_start:
        exercise_logs = exercise_logs.filter(completion_timestamp__gte=period_start)
        video_logs = video_logs.filter(completion_timestamp__gte=period_start)
        login_logs = login_logs.filter(start_datetime__gte=period_start)
    if period_end:
        exercise_logs = exercise_logs.filter(completion_timestamp__lte=period_end)
        video_logs = video_logs.filter(completion_timestamp__lte=period_end)
        login_logs = login_logs.filter(end_datetime__lte=period_end)


    # Force results in a single query
    exercise_logs = list(exercise_logs.values("exercise_id", "user__pk"))
    video_logs = list(video_logs.values("video_id", "user__pk"))
    login_logs = list(login_logs.values("activity_type", "total_seconds", "user__pk"))

    for user in users:
        user_data[user.pk] = OrderedDict()
        user_data[user.pk]["id"] = user.pk
        user_data[user.pk]["first_name"] = user.first_name
        user_data[user.pk]["last_name"] = user.last_name
        user_data[user.pk]["username"] = user.username
        user_data[user.pk]["group"] = user.group


        user_data[user.pk]["total_report_views"] = 0#report_stats["count__sum"] or 0
        user_data[user.pk]["total_logins"] =0# login_stats["count__sum"] or 0
        user_data[user.pk]["total_hours"] = 0#login_stats["total_seconds__sum"] or 0)/3600.

        user_data[user.pk]["total_exercises"] = 0
        user_data[user.pk]["pct_mastery"] = 0.
        user_data[user.pk]["exercises_mastered"] = []

        user_data[user.pk]["total_videos"] = 0
        user_data[user.pk]["videos_watched"] = []


    for elog in exercise_logs:
        user_data[elog["user__pk"]]["total_exercises"] += 1
        user_data[elog["user__pk"]]["pct_mastery"] += 1. / num_exercises
        user_data[elog["user__pk"]]["exercises_mastered"].append(elog["exercise_id"])

    for vlog in video_logs:
        user_data[vlog["user__pk"]]["total_videos"] += 1
        user_data[vlog["user__pk"]]["videos_watched"].append(vlog["video_id"])

    for llog in login_logs:
        if llog["activity_type"] == UserLog.get_activity_int("coachreport"):
            user_data[llog["user__pk"]]["total_report_views"] += 1
        elif llog["activity_type"] == UserLog.get_activity_int("login"):
            user_data[llog["user__pk"]]["total_hours"] += (llog["total_seconds"]) / 3600.
            user_data[llog["user__pk"]]["total_logins"] += 1

    for group in list(groups) + [None]*(group_id==None or _(group_id)==_("Ungrouped")):  # None for ungrouped, if no group_id passed.
        group_pk = getattr(group, "pk", None)
        group_name = getattr(group, "name", _("Ungrouped"))
        group_data[group_pk] = {
            "id": group_pk,
            "name": group_name,
            "total_logins": 0,
            "total_hours": 0,
            "total_users": 0,
            "total_videos": 0,
            "total_exercises": 0,
            "pct_mastery": 0,
        }

    # Add group data.  Allow a fake group "Ungrouped"
    for user in users:
        group_pk = getattr(user.group, "pk", None)
        group_data[group_pk]["total_users"] += 1
        group_data[group_pk]["total_logins"] += user_data[user.pk]["total_logins"]
        group_data[group_pk]["total_hours"] += user_data[user.pk]["total_hours"]
        group_data[group_pk]["total_videos"] += user_data[user.pk]["total_videos"]
        group_data[group_pk]["total_exercises"] += user_data[user.pk]["total_exercises"]

        total_mastery_so_far = (group_data[group_pk]["pct_mastery"] * (group_data[group_pk]["total_users"] - 1) + user_data[user.pk]["pct_mastery"])
        group_data[group_pk]["pct_mastery"] =  total_mastery_so_far / group_data[group_pk]["total_users"]

    return (user_data.values(), group_data.values())


# context functions

def control_panel_context(request, **kwargs):
    context = {}
    for key, val in kwargs.iteritems():
        if key.endswith("_id") and val == "None":
            kwargs[key] = None

    device = Device.get_own_device()
    default_zone = device.get_zone()

    if "zone_id" in kwargs:
        context["zone"] = get_object_or_None(Zone, pk=kwargs["zone_id"]) if kwargs["zone_id"] else default_zone
        context["zone_id"] = kwargs["zone_id"] or (default_zone and default_zone.id) or "None"
    if "facility_id" in kwargs:
        context["facility"] = get_object_or_404(Facility, pk=kwargs["facility_id"]) if kwargs["facility_id"] != "new" else None
        context["facility_id"] = kwargs["facility_id"] or "None"
    if "group_id" in kwargs:
        context["group"] = get_object_or_None(FacilityGroup, pk=kwargs["group_id"])
        context["group_id"] = kwargs["group_id"] or "None"
    if "device_id" in kwargs:
        context["device"] = get_object_or_404(Device, pk=kwargs["device_id"])
        context["device_id"] = kwargs["device_id"] or "None"
    return context


def local_device_context(request):
    database_path = settings.DATABASES["default"]["NAME"]
    current_version = request.GET.get("version", VERSION)  # allows easy development by passing a different version

    return {
        "software_version": current_version,
        "software_release_date": VERSION_INFO[current_version]["release_date"],
        "install_dir": os.path.realpath(os.path.join(settings.PROJECT_PATH, "..")),
        "database_last_updated": datetime.datetime.fromtimestamp(os.path.getctime(database_path)),
        "database_size": os.stat(settings.DATABASES["default"]["NAME"]).st_size / float(1024**2),
    }

