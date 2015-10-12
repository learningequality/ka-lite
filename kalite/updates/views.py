import sys

from annoying.decorators import render_to

from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib import messages
from django.conf import settings

from .models import VideoFile
from kalite.i18n import get_installed_language_packs
from kalite.shared.decorators.auth import require_admin
from securesync.models import Device
from securesync.devices.decorators import require_registration
from kalite.topic_tools.settings import DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP


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
    if getattr(settings, 'USING_RASPBERRY_PI', False):
        messages.warning(request, _('For low-powered devices like the Raspberry Pi, please download less than 25 videos at a time.'))

    if DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP or sys.platform == 'darwin':
        messages.warning(request, _('After video download, the server must be restarted for them to be available to users.'))
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
