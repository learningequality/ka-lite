import copy
import datetime
import json
import os
import re 
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page

import settings
import version
from config.models import Settings
from control_panel.views import user_management_context
from main import topicdata
from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser, FacilityGroup, Device
from securesync.views import require_admin, facility_required
from shared import topic_tools
from shared.decorators import require_admin
from shared.jobs import force_job
from utils.internet import am_i_online, JsonResponse


def update_context(request):
    device = Device.get_own_device()
    zone = device.get_zone()

    context = {
        "registered": Settings.get("registered"),
        "zone_id": zone.id if zone else None,
        "device_id": device.id,
    }
    return context


@require_admin
@render_to("updates/update.html")
def update(request):
    context = update_context(request)
    context.update({
        "registered": Settings.get("registered"),
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
    })
    return context

@require_admin
@render_to("updates/update.html")
def update(request):
    context = update_context(request)
    return context

@require_admin
@render_to("updates/update_videos.html")
def update_videos(request):
    call_command("videoscan")  # Could potentially be very slow, blocking request.
    force_job("videodownload", "Download Videos")

    context = update_context(request)
    context.update({
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
    })
    return context


@require_admin
@render_to("updates/update_subtitles.html")
def update_subtitles(request):
    force_job("subtitledownload", "Download Subtitles")

    default_language = Settings.get("subtitle_language") or "en"

    context = update_context(request)
    context.update({
        "default_language": default_language,
    })
    return context


@require_admin
@render_to("updates/update_software.html")
def update_software(request):
    database_path = settings.DATABASES["default"]["NAME"]
    current_version = request.GET.get("version", version.VERSION)  # allows easy development by passing a different version

    context = update_context(request)
    context.update({
        "software_version": current_version,
        "software_release_date": version.VERSION_INFO[current_version]["release_date"],
        "install_dir": os.path.realpath(os.path.join(settings.PROJECT_PATH, "..")),
        "database_last_updated": datetime.datetime.fromtimestamp(os.path.getctime(database_path)),
        "database_size": os.stat(settings.DATABASES["default"]["NAME"]).st_size / float(1024**2),
    })
    return context
