import copy
import datetime
import json
import os
import re
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page

import settings
import version
from .models import VideoFile
from chronograph import force_job
from control_panel.views import local_device_context
from i18n import lcode_to_ietf, get_installed_language_packs, lang_best_name, get_language_name
from main import topic_tools
from securesync.models import Device
from securesync.devices import require_registration
from securesync.views import require_admin
from shared.decorators import require_admin
from utils.internet import am_i_online, JsonResponse


def update_context(request):
    device = Device.get_own_device()
    zone = device.get_zone()

    context = {
        "registered": Device.get_own_device().is_registered(),
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
@require_registration(ugettext_lazy("video downloads"))
@render_to("updates/update_videos.html")
def update_videos(request, max_to_show=4):
    installed_languages = get_installed_language_packs(force=True).copy() # we copy to avoid changing the original installed language list
    default_language_name = lang_best_name(installed_languages.pop(lcode_to_ietf(request.session["default_language"])))
    languages_to_show = [lang_best_name(l) for l in installed_languages.values()[:max_to_show]]
    other_languages_count = max(0, len(installed_languages) - max_to_show)

    context = update_context(request)
    context.update({
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
        "languages": languages_to_show,
        "default_language_name": default_language_name,
        "other_languages_count": other_languages_count,
    })
    return context


@require_admin
@require_registration(ugettext_lazy("language packs"))
@render_to("updates/update_languages.html")
def update_languages(request):
    # also refresh language choices here if ever updates js framework fails, but the language was downloaded anyway
    installed_languages = get_installed_language_packs(force=True)

    # here we want to reference the language meta data we've loaded into memory
    context = update_context(request)
    context.update({
        "installed_languages": installed_languages.values(),
    })
    return context


@require_admin
@render_to("updates/update_software.html")
def update_software(request):
    context = update_context(request)
    context.update(local_device_context(request))
    return context
