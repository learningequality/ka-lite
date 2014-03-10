import os

from django.conf import settings

if settings.USE_DEBUG_TOOLBAR:
    assert settings.CACHE_TIME == 0, "Debug toolbar must be set in conjunction with CACHE_TIME=0"
