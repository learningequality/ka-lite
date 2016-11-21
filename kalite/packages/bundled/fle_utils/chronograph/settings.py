try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


########################
# Set module settings
########################

CRONSERVER_FREQUENCY = getattr(local_settings, "CRONSERVER_FREQUENCY", 600) # 10 mins (in seconds)
