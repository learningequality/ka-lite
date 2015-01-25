try:
    import local_settings
except ImportError:
    local_settings = object()

INSTALLED_APPS = tuple()
