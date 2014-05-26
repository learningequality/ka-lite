"""

"""
from django.conf import settings

from kalite import version


# TODO(jamalex): this should be calculated more intelligently, and incorporated into a template tag
# (see https://github.com/learningequality/ka-lite/issues/1161)
BUILD_ID = version.VERSION_INFO[version.VERSION]["git_commit"][0:8]

def custom(request):
    return {
        "restricted": settings.DISABLE_SELF_ADMIN,
    }
