try:
    from kalite import local_settings
except ImportError:
    local_settings = object()

API_LIMIT_PER_PAGE = 0   # no limit

QUIZ_REPEATS = 3
