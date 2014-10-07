try:
    import local_settings
except ImportError:
    local_settings = object()

API_LIMIT_PER_PAGE = 0   # no limit

INSTALLED_APPS = (
    "tastypie",
    "kalite.contentload",
    "kalite.main",
)

QUIZ_REPEATS = 3