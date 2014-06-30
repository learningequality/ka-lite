from django.conf import settings

from fle_utils.importing import import_all_child_modules


import_all_child_modules()

if settings.USE_DEBUG_TOOLBAR:
    assert settings.CACHE_TIME == 0, "Debug toolbar must be set in conjunction with CACHE_TIME=0"
