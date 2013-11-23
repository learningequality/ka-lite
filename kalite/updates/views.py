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
from .models import VideoFile
from config.models import Settings
from control_panel.views import local_device_context, user_management_context
from main import topicdata
from securesync.models import Facility, FacilityUser, FacilityGroup, Device
from securesync.views import require_admin, facility_required
from shared import topic_tools
from shared.decorators import require_admin
from shared.i18n import get_installed_languages
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
@render_to("updates/landing_page.html")
def update(request):
    context = update_context(request)
    return context

@require_admin
@render_to("updates/update_videos.html")
def update_videos(request):
    call_command("videoscan")  # Could potentially be very slow, blocking request.
    force_job("videodownload", _("Download Videos"))  # async request

    context = update_context(request)
    context.update({
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
    })
    return context


@require_admin
@render_to("updates/update_languages.html")
def update_languages(request):
    # here we want to reference the language meta data we've loaded into memory
    context = update_context(request)

    context.update({
        "installed_languages": get_installed_languages(),
        "default_language": settings.LANGUAGE_CODE,
    })

    return context


@require_admin
@render_to("updates/update_software.html")
def update_software(request):
    context = update_context(request)
    context.update(local_device_context(request))
    return context
