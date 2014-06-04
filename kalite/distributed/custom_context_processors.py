"""
Things we want to send to every template within the KA Lite app.

These include:
* Metadata about the central server (for syncing, getting content, language packs, etc)
* App settings, including version / build ID
"""
from django.conf import settings

from kalite import version


def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "distributed/base.html",
        "is_central": False,
        "settings": settings,
        "VERSION": version.VERSION,
        "True": True,
        "False": False
    }
