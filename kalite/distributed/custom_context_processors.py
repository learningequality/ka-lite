"""
Things we want to send to every template within the KA Lite app.

These include:
* Metadata about the central server (for syncing, getting content, language packs, etc)
* App settings, including version / build ID
"""
from django.conf import settings

from kalite import version


# TODO(jamalex): this should be calculated more intelligently, and incorporated into a template tag
# (see https://github.com/learningequality/ka-lite/issues/1161)
BUILD_ID = version.VERSION_INFO[version.VERSION]["git_commit"][0:8]

def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "distributed/base.html",
        "is_central": False,
        "settings": settings,
        "restricted": settings.DISABLE_SELF_ADMIN,
        "VERSION": version.VERSION,
        "BUILD_ID": BUILD_ID,
    }
