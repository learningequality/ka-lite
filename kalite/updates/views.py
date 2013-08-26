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
from shared.decorators import require_admin
from shared.jobs import force_job
from kalite.utils import topic_tools
from kalite.utils.internet import am_i_online, JsonResponse
from kalite.utils.videos import video_connection_is_available


@require_admin
@render_to("updates/update.html")
def update(request):

    am_i_online = video_connection_is_available()
    if not am_i_online:
        messages.warning(request, _("No internet connection was detected.  You must be online to download videos or subtitles."))

    device = Device.get_own_device()
    zone = device.get_zone()

    context = {
        "am_i_online": am_i_online,
        "registered": Settings.get("registered"),
        "zone_id": zone.id if zone else None,
        "device_id": device.id,
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
    }
    return context

@require_admin
@render_to("updates/update_videos.html")
def update_videos(request):
    call_command("videoscan")  # Could potentially be very slow, blocking request.
    force_job("videodownload", "Download Videos")

    context = {
        "am_i_online": True,
    }
    return context


@require_admin
@render_to("updates/update_subtitles.html")
def update_subtitles(request):
    force_job("subtitledownload", "Download Subtitles")
    language_lookup = topicdata.LANGUAGE_LOOKUP
    language_list = topicdata.LANGUAGE_LIST
    default_language = Settings.get("subtitle_language") or "en"
    if default_language not in language_list:
        language_list.append(default_language)
    languages = [{"id": key, "name": language_lookup[key]} for key in language_list]
    languages = sorted(languages, key=lambda k: k["name"])

    context = {
        "languages": languages,
        "default_language": default_language,
        "am_i_online": True,
    }
    return context


@require_admin
@render_to("updates/update_software.html")
def update_software(request):
    database_path = settings.DATABASES["default"]["NAME"]
    current_version = request.GET.get("version", version.VERSION)  # allows easy development by passing a different version

    context = {
        "software_version": current_version,
        "software_release_date": version.VERSION_INFO[current_version]["release_date"],
        "install_dir": os.path.realpath(os.path.join(settings.PROJECT_PATH, "..")),
        "database_last_updated": datetime.datetime.fromtimestamp(os.path.getctime(database_path)),
        "database_size": os.stat(settings.DATABASES["default"]["NAME"]).st_size / float(1024**2),
        "device_id": Device.get_own_device().id,
    }
    return context
