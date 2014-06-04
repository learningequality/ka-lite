import copy
import datetime
import git
import json
import os
import re
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseServerError
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page

from .models import VideoFile
from fle_utils.chronograph import force_job
from fle_utils.internet import am_i_online, JsonResponse
from kalite import topic_tools
from kalite.control_panel.views import local_install_context
from kalite.i18n import get_installed_language_packs, get_language_name
from kalite.shared.decorators import require_admin
from securesync.models import Device
from securesync.devices import require_registration


def update_context(request):
    device = Device.get_own_device()
    zone = device.get_zone()

    context = {
        "is_registered": device.is_registered(),
        "zone_id": zone.id if zone else None,
        "device_id": device.id,
    }
    return context


@require_admin
@require_registration(ugettext_lazy("video downloads"))
@render_to("updates/update_videos.html")
def update_videos(request, max_to_show=4):
    context = update_context(request)
    context.update({
        "video_count": VideoFile.objects.filter(percent_complete=100).count(),
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
    context.update(local_install_context(request))

    try:
        repo = git.Repo(os.path.dirname(__file__))
        software_version = repo.git.describe()
        is_git_repo = bool(repo)
    except git.exc.InvalidGitRepositoryError:
        is_git_repo = False
        software_version = None

    context.update({
        "is_git_repo": str(is_git_repo).lower(), # lower to make it look like JS syntax
        "git_software_version": software_version,
    })

    return context

