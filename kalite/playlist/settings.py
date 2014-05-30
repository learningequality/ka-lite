try:
    import local_settings
except ImportError:
    local_settings = object()

API_LIMIT_PER_PAGE = 0   # no limit

INSTALLED_APPS = getattr(local_settings, 'INSTALLED_APPS', tuple())
INSTALLED_APPS = (
    "tastypie",
    "kalite.khanload",
    "kalite.main",
) + INSTALLED_APPS
