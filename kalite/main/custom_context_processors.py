import settings
import version

# TODO(jamalex): this should be calculated more intelligently, and incorporated into a template tag
# (see https://github.com/learningequality/ka-lite/issues/1161)
BUILD_ID = version.VERSION_INFO[version.VERSION]["git_commit"][0:8]

def custom(request):
    return {
        "central_server_host": settings.CENTRAL_SERVER_HOST,
        "securesync_protocol": settings.SECURESYNC_PROTOCOL,
        "base_template": "base.html",
        "is_central": False,
        "settings": settings,
        "restricted": settings.package_selected("UserRestricted"),
        "VERSION": version.VERSION,
        "BUILD_ID": BUILD_ID,
    }
