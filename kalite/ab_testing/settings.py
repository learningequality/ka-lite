try:
    import local_settings
except ImportError:
    local_settings = object()

INSTALLED_APPS = tuple()

#################################
# Toggling motivational features
#################################
TURN_OFF_MOTIVATIONAL_FEATURES = getattr(local_settings, 'TURN_OFF_MOTIVATIONAL_FEATURES', False)
