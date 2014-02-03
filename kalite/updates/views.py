import copy
import datetime
import json
import os
import re
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

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
from i18n.middleware import set_language_choices
from securesync.models import Facility, FacilityUser, FacilityGroup, Device
from securesync.views import require_admin, facility_required
from shared import topic_tools
from shared.decorators import require_admin
from shared.i18n import lcode_to_ietf, get_installed_language_packs, lang_best_name
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
def update_videos(request, max_to_show=4):
    call_command("videoscan")  # Could potentially be very slow, blocking request.
    force_job("videodownload", _("Download Videos"))  # async request

    installed_languages = set_language_choices(request, force=True)
    if request.is_django_user or not request.session["facility_user"].default_language:
        default_language = Settings.get("default_language", "en")
    elif not request.is_django_user and request.session["facility_user"].default_language:
        default_language = request.session["facility_user"].default_language
    default_language = lang_best_name(installed_languages.pop(default_language))
    languages_to_show = [lang_best_name(l) for l in installed_languages.values()[:max_to_show]]
    other_languages_count = max(0, len(installed_languages) - max_to_show)

    context = update_context(request)
    context.update({
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
        "languages": languages_to_show,
        "default_language": default_language,
        "other_languages_count": other_languages_count,
    })
    return context


@require_admin
@render_to("updates/update_languages.html")
def update_languages(request):
    # also refresh language choices here if ever updates js framework fails, but the language was downloaded anyway
    set_language_choices(request, force=True)

    # here we want to reference the language meta data we've loaded into memory
    context = update_context(request)
    context.update({
        "installed_languages": request.session['language_choices'].values(),
    })
    return context


@require_admin
@render_to("updates/update_software.html")
def update_software(request):
    context = update_context(request)
    context.update(local_device_context(request))
    return context
