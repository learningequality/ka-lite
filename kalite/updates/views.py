import sys

from annoying.decorators import render_to

from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib import messages
from django.conf import settings

from kalite.i18n.base import get_installed_language_packs
from kalite.shared.decorators.auth import require_admin
from securesync.models import Device
from securesync.devices.decorators import require_registration

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
