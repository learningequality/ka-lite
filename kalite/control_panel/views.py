"""
"""
import datetime
import dateutil
import re
import os
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from collections_local_copy import OrderedDict

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.db.models import Max
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from .forms import ZoneForm, UploadFileForm, DateRangeForm
from fle_utils.chronograph.models import Job
from fle_utils.django_utils.paginate import paginate_data
from fle_utils.internet.decorators import render_to_csv
from securesync.models import Device, Zone, SyncSession
from kalite.dynamic_assets.decorators import dynamic_settings
from kalite.coachreports.views import student_view_context
from kalite.facility.utils import get_users_from_group
from kalite.facility.decorators import facility_required
from kalite.facility.forms import FacilityForm
from kalite.facility.models import Facility, FacilityUser, FacilityGroup
from kalite.main.models import ExerciseLog, VideoLog, UserLog, UserLogSummary
from kalite.shared.decorators.auth import require_authorized_admin, require_authorized_access_to_student_data
from kalite.topic_tools import get_exercise_cache
from kalite.version import VERSION, VERSION_INFO


UNGROUPED = "Ungrouped"


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
    context = process_zone_form(request, zone_id)
    if request.method == "POST" and context["form"].is_valid():
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

    context.update({"form": form})
    return context


@require_authorized_admin
@render_to("control_panel/zone_management.html")
def zone_management(request, zone_id="None"):
    context = control_panel_context(request, zone_id=zone_id)
    own_device = Device.get_own_device()

    if not context["zone"] and (zone_id != "None" or own_device.get_zone() or settings.CENTRAL_SERVER):
        raise Http404()  # on distributed server, we can make due if they're not registered.

    # Denote the zone as headless or not
    if context["zone"]:
        is_headless_zone = re.search(r'Zone for public key ', context["zone"].name)
    else:
        is_headless_zone = False

    # Accumulate device data
    device_data = OrderedDict()
    if context["zone"]:
        devices = Device.objects.filter(devicezone__zone=context["zone"])
    else:
        devices = Device.objects.filter(devicemetadata__is_own_device=True)

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
            "meta_data_in_need": check_meta_data(facility),
            "last_time_used":   exercise_activity.order_by("-completion_timestamp")[0:1] if user_activity.count() == 0 else user_activity.order_by("-last_activity_datetime", "-end_datetime")[0],
        }

    context.update({
        "is_headless_zone": is_headless_zone,
        "facilities": facility_data,
        "missing_meta": any([facility['meta_data_in_need'] for facility in facility_data.values()]),
        "devices": device_data,
        "upload_form": UploadFileForm(),
        "own_device_is_trusted": Device.get_own_device().get_metadata().is_trusted,
    })
    if not settings.CENTRAL_SERVER:
        context["base_template"] = "distributed/base_manage.html"
    context.update(set_clock_context(request))

    return context


@require_authorized_admin
@render_to("control_panel/data_export.html")
def data_export(request):

    zone_id = request.GET.get("zone_id", "")
    facility_id = request.GET.get("facility_id", "")
    group_id = request.GET.get("group_id", "")

    if 'facility_user' in request.session:
        facility_id = request.session['facility_user'].facility.id

    if zone_id:
        zone = Zone.objects.get(id=zone_id)
    else:
        zone = ""

    if settings.CENTRAL_SERVER:
        # TODO(dylanjbarth and benjaoming): this looks awful
        from central.models import Organization
        all_zones_url = reverse("api_dispatch_list", kwargs={"resource_name": "zone"})
        if zone_id:
            org = Zone.objects.get(id=zone_id).get_org()
            org_id = org.id
        else:
            org_id = request.GET.get("org_id", "")
            if not org_id:
                return HttpResponseNotFound()
            else:
                org = Organization.objects.get(id=org_id)
    else:
        all_zones_url = ""
        org = ""
        org_id = ""

    context = {
        "is_central": settings.CENTRAL_SERVER,
        "org_id": org_id,
        "zone_id": zone_id,
        "facility_id": facility_id,
        "group_id": group_id,
        "all_zones_url": all_zones_url,
        "org": org,
        "zone": zone,
    }

    return context

@require_authorized_admin
@render_to("control_panel/device_management.html")
def device_management(request, device_id, zone_id=None, per_page=None, cur_page=None):
    context = control_panel_context(request, zone_id=zone_id, device_id=device_id)

    #Get pagination details
    cur_page = cur_page or request.REQUEST.get("cur_page", "1")
    per_page = per_page or request.REQUEST.get("per_page", "10")

    # Retrieve sync sessions
    all_sessions = SyncSession.objects.filter(client_device=context["device"])
    total_sessions = all_sessions.count()
    shown_sessions = list(all_sessions.order_by("-timestamp").values("timestamp", "ip", "models_uploaded", "models_downloaded", "errors"))

    session_pages, page_urls = paginate_data(request, shown_sessions, page=cur_page, per_page=per_page)

    sync_job = get_object_or_None(Job, command="syncmodels")

    context.update({
        "session_pages": session_pages,
        "page_urls": page_urls,
        "total_sessions": total_sessions,
        "device_version": total_sessions and all_sessions[0].client_version or None,
        "device_os": total_sessions and all_sessions[0].client_os or None,
        "is_own_device": not settings.CENTRAL_SERVER and device_id == Device.get_own_device().id,
        "sync_job": sync_job,
    })

    # If local (and, for security purposes, a distributed server), get device metadata
    if context["is_own_device"]:
        database_path = settings.DATABASES["default"]["NAME"]
        current_version = request.GET.get("version", VERSION)  # allows easy development by passing a different version

        context.update({
            "software_version": current_version,
            "software_release_date": VERSION_INFO().get(
                current_version, {}
            ).get("release_date", "Unknown"),
            "install_dir": settings.SOURCE_DIR if settings.IS_SOURCE else "Not applicable (not a source installation)",
            "database_last_updated": datetime.datetime.fromtimestamp(os.path.getctime(database_path)),
            "database_size": os.stat(settings.DATABASES["default"]["NAME"]).st_size / float(1024**2),
        })

    return context


@require_authorized_admin
@render_to("control_panel/facility.html")
@dynamic_settings
def facility_form(request, ds, facility_id=None, zone_id=None):
    if request.is_teacher and not ds["facility"].teacher_can_edit_facilities:
        return HttpResponseForbidden()

    context = control_panel_context(request, zone_id=zone_id, facility_id=facility_id)

    if request.method != "POST":
        form = FacilityForm(instance=context["facility"])

    else:
        form = FacilityForm(data=request.POST, instance=context["facility"])
        if not form.is_valid():
            messages.error(request, _("Failed to save the facility; please review errors below."))
        else:
            form.instance.zone_fallback = get_object_or_None(Zone, pk=zone_id)

            if settings.CENTRAL_SERVER:
                assert form.instance.zone_fallback is not None

            form.save()
            messages.success(request, _("The facility '%(facility_name)s' has been successfully saved!") % {"facility_name": form.instance.name})
            return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": zone_id}))

    context.update({"form": form})
    return context


@require_authorized_admin
@render_to_csv(["students"], key_label="user_id", order="stacked")
def facility_management_csv(request, facility, group_id=None, zone_id=None, frequency=None, period_start="", period_end="", user_type=None):
    """NOTE: THIS IS NOT A VIEW FUNCTION"""
    assert request.method == "POST", "facility_management_csv must be accessed via POST"

    # Search form for errors.
    form = DateRangeForm(data=request.POST)
    if not form.is_valid():
        raise Exception(_("Error parsing date range: %(error_msg)s.  Please review and re-submit.") % form.errors.as_data())

    frequency = frequency or request.GET.get ("frequency", "months")
    period_start = period_start or form.data["period_start"]
    period_end = period_end or form.data["period_end"]
    (period_start, period_end) = _get_date_range(frequency, period_start, period_end)


    # Basic data
    context = control_panel_context(request, zone_id=zone_id, facility_id=facility.id)
    group = group_id and get_object_or_None(FacilityGroup, id=group_id)
    groups = FacilityGroup.objects.filter(facility=context["facility"]).order_by("name")
    # coaches = get_users_from_group(user_type="coaches", group_id=group_id, facility=facility)
    students = get_users_from_group(user_type="students", group_id=group_id, facility=facility)

    (student_data, group_data) = _get_user_usage_data(students, groups, group_id=group_id, period_start=period_start, period_end=period_end)
    # (coach_data, coach_group_data) = _get_user_usage_data(coaches, period_start=period_start, period_end=period_end)

    context.update({
        "students": student_data,  # raw data
        # "coaches": coach_data,  # raw data
    })
    return context


@facility_required
@require_authorized_admin
@render_to("control_panel/facility_management.html")
@dynamic_settings
def facility_management(request, ds, facility, group_id=None, zone_id=None, per_page=25):

    ungrouped_id = UNGROUPED

    if request.method == "POST" and request.GET.get("format") == "csv":
        try:
            return facility_management_csv(request, facility=facility, group_id=group_id, zone_id=zone_id)
        except Exception as e:
            messages.error(request, e)

    context = control_panel_context(request, zone_id=zone_id, facility_id=facility.id)

    #Get pagination details
    coach_page = request.REQUEST.get("coaches_page", "1")
    coach_per_page = request.REQUEST.get("coaches_per_page", "5")
    student_page = request.REQUEST.get("students_page", "1")
    student_per_page = request.REQUEST.get("students_per_page", "25" if group_id else "10")

    # Basic data
    group = group_id and get_object_or_None(FacilityGroup, id=group_id)
    groups = FacilityGroup.objects.filter(facility=context["facility"]).order_by("name")
    coaches = get_users_from_group(user_type="coaches", group_id=group_id, facility=facility)
    students = get_users_from_group(user_type="students", group_id=group_id, facility=facility)

    (student_data, group_data) = _get_user_usage_data(students, groups, group_id=group_id)
    (coach_data, coach_group_data) = _get_user_usage_data(coaches)

    coach_pages, coach_urls = paginate_data(request, coach_data.values(), data_type="coaches", page=coach_page, per_page=coach_per_page)
    student_pages, student_urls = paginate_data(request, student_data.values(), data_type="students", page=student_page, per_page=student_per_page)

    # Now prep the CSV form (even though we won't process it)
    form = DateRangeForm(data=request.POST) if request.method == "POST" else DateRangeForm()
    frequency = request.GET.get("frequency", "months")
    period_start = form.data.get("period_start")
    period_end = form.data.get("period_end")
    (period_start, period_end) = _get_date_range(frequency, period_start, period_end)

    # Collate data for all groups
    groups = group_data.values()

    # If group_id exists, extract data for that group
    if group_id:
        if group_id == ungrouped_id:
            group_id_index = next(index for (index, d) in enumerate(group_data.values()) if d["name"] == _(UNGROUPED))
        else:
            group_id_index = next(index for (index, d) in enumerate(group_data.values()) if d["id"] == group_id)
        group_data = group_data.values()[group_id_index]
    else:
        group_data = {}

    context.update({
        "form": form,
        "date_range": [str(period_start), str(period_end)],
        "group": group,
        "group_id": group_id,
        "group_data": group_data,
        "groups": groups, # sends dict if group page, list of group data otherwise
        "student_pages": student_pages,  # paginated data
        "coach_pages": coach_pages,  # paginated data
        "ds": ds,
        "page_urls": {
            "coaches": coach_urls,
            "students": student_urls,
        },
        "ungrouped_id": ungrouped_id
    })

    if not settings.CENTRAL_SERVER:
        context["base_template"] = "distributed/base_manage.html"

    return context


@require_authorized_access_to_student_data
@render_to("control_panel/account_management.html")
def account_management(request):

    # Only log 'coachreport' activity for students,
    #   (otherwise it's hard to compare teachers)
    if "facility_user" in request.session and not request.session["facility_user"].is_teacher:
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.error("Failed to update student userlog activity: %s" % e)

    c = student_view_context(request)
    c['restricted'] = settings.DISABLE_SELF_ADMIN
    return c


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
    num_exercises = len(get_exercise_cache())
    user_data = OrderedDict()
    group_data = OrderedDict()

    # Make queries efficiently
    exercise_logs = ExerciseLog.objects.filter(user__in=users, complete=True)
    video_logs = VideoLog.objects.filter(user__in=users, total_seconds_watched__gt=0)
    login_logs = UserLogSummary.objects.filter(user__in=users)

    # filter results
    login_logs = login_logs.filter(total_seconds__gt=0)
    if period_start:
        exercise_logs = exercise_logs.filter(completion_timestamp__gte=period_start)
        video_logs = video_logs.filter(completion_timestamp__gte=period_start)
    if period_end:
        # MUST: Fix the midnight bug where period end covers up to the prior day only because
        # period end is datetime(year, month, day, hour=0, minute=0), meaning midnight of previous day.
        # Example:
        #   If period_end == '2014-12-01', we cannot include the records dated '2014-12-01 09:30'.
        #   So to fix this, we change it to '2014-12-01 23:59.999999'.
        period_end = dateutil.parser.parse(period_end)
        period_end = period_end + dateutil.relativedelta.relativedelta(days=+1, microseconds=-1)
        exercise_logs = exercise_logs.filter(completion_timestamp__lte=period_end)
        video_logs = video_logs.filter(completion_timestamp__lte=period_end)
    if period_start and period_end:
        exercise_logs = exercise_logs.filter(Q(completion_timestamp__gte=period_start) &
                                             Q(completion_timestamp__lte=period_end))

        q1 = Q(completion_timestamp__isnull=False) & \
            Q(completion_timestamp__gte=period_start) & \
            Q(completion_timestamp__lte=period_end)
        video_logs = video_logs.filter(q1)

        login_q1 = Q(start_datetime__gte=period_start) & Q(start_datetime__lte=period_end) & \
            Q(end_datetime__gte=period_start) & Q(end_datetime__lte=period_end)
        login_logs = login_logs.filter(login_q1)
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

    for group in list(groups) + [None]*(group_id==None or group_id==UNGROUPED):  # None for ungrouped, if no group_id passed.
        group_pk = getattr(group, "pk", None)
        group_name = getattr(group, "name", _(UNGROUPED))
        group_title = getattr(group, "title", _(UNGROUPED))
        group_data[group_pk] = {
            "id": group_pk,
            "name": group_name,
            "title": group_title,
            "total_logins": 0,
            "total_hours": 0,
            "total_users": 0,
            "total_videos": 0,
            "total_exercises": 0,
            "pct_mastery": 0,
        }

    # Add group data.  Allow a fake group UNGROUPED
    for user in users:
        group_pk = getattr(user.group, "pk", None)
        if group_pk not in group_data:
            logging.error("User %s still in nonexistent group %s!" % (user.id, group_pk))
            continue
        group_data[group_pk]["total_users"] += 1
        group_data[group_pk]["total_logins"] += user_data[user.pk]["total_logins"]
        group_data[group_pk]["total_hours"] += user_data[user.pk]["total_hours"]
        group_data[group_pk]["total_videos"] += user_data[user.pk]["total_videos"]
        group_data[group_pk]["total_exercises"] += user_data[user.pk]["total_exercises"]

        total_mastery_so_far = (group_data[group_pk]["pct_mastery"] * (group_data[group_pk]["total_users"] - 1) + user_data[user.pk]["pct_mastery"])
        group_data[group_pk]["pct_mastery"] =  total_mastery_so_far / group_data[group_pk]["total_users"]

    if len(group_data) == 1 and group_data.has_key(None):
        if not group_data[None]["total_users"]:
            del group_data[None]

    return (user_data, group_data)


def check_meta_data(facility):
    '''Checks whether any metadata is missing for the specified facility.

    Args: 
      facility (Facility instance): facility to check for missing metadata
 
    Returns:
      bool: True if one or more metadata fields are missing'''

    check_fields = ['user_count', 'latitude', 'longitude', 'address', 'contact_name', 'contact_phone', 'contact_email']
    return any([ (getattr(facility, field, None) is None or getattr(facility, field)=='') for field in check_fields])


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
