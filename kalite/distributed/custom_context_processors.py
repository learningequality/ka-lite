"""
Things we want to send to every template within the KA Lite app.

These include:
* Metadata about the central server (for syncing, getting content, language packs, etc)
* App settings, including version / build ID
"""
import json
import os

from django.conf import settings
from django.utils.translation import ugettext as _

from kalite import version
from kalite.topic_tools import settings as topic_tools_settings

channel_data = {}

def custom(request):
    global channel_data

    channel_data_trans = {}

    # MUST: Translation must happen inside this function because it will NOT work if it is outside
    # because that part of the code only runs once when this module is loaded/imported.
    if not channel_data:
        # Parsing a whole JSON file just to load the settings is not nice
        try:
            channel_data = json.load(open(os.path.join(topic_tools_settings.CHANNEL_DATA_PATH, "channel_data.json"), 'r'))
        except IOError:
            channel_data = {}

    for key, value in channel_data.items():
        channel_data_trans[key] = _(value)

    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "central_server_domain": settings.CENTRAL_SERVER_DOMAIN,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "distributed/base.html",
        "channel_data": channel_data_trans,
        "channel": topic_tools_settings.CHANNEL,
        "is_central": False,
        "settings": settings,
        "VERSION": version.VERSION,
        "SHORTVERSION": version.SHORTVERSION,
        "True": True,
        "False": False,
        "is_config_package_nalanda": "nalanda" in settings.CONFIG_PACKAGE,
        "inline_help": getattr(settings, "INLINE_HELP", False)
    }
