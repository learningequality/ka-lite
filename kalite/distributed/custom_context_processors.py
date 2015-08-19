"""
Things we want to send to every template within the KA Lite app.

These include:
* Metadata about the central server (for syncing, getting content, language packs, etc)
* App settings, including version / build ID
"""
from django.conf import settings
from django.utils.translation import ugettext as _

from kalite import version

channel_data = {}


def custom(request):

    # MUST: Translation must happen inside this function because it will NOT work if it is outside
    # because that part of the code only runs once when this module is loaded/imported.
    for key, value in settings.CHANNEL_DATA.items():
        channel_data[key] = _(value)

    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "central_server_domain": settings.CENTRAL_SERVER_DOMAIN,
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
        "is_config_package_nalanda": "nalanda" in settings.CONFIG_PACKAGE,
        "inline_help": getattr(settings, "INLINE_HELP", False)
    }
