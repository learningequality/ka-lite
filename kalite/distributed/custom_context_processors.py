"""
Things we want to send to every template within the KA Lite app.

These include:
* Metadata about the central server (for syncing, getting content, language packs, etc)
* App settings, including version / build ID
"""
from django.conf import settings

from kalite import version

from django.utils.translation import ugettext as _

channel_data = {}

for key, value in settings.CHANNEL_DATA.items():
    channel_data[key] = _(value)


def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "distributed/base.html",
        "channel_data": channel_data,
        "channel": settings.CHANNEL,
        "is_central": False,
        "settings": settings,
        "VERSION": version.VERSION,
        "SHORTVERSION": version.SHORTVERSION,
        "True": True,
        "False": False,
        "is_config_package_nalanda": "nalanda" in settings.CONFIG_PACKAGE
    }
