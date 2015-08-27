# Import local settings, for overriding
try:
    from kalite import local_settings
except ImportError:
    local_settings = object()

#######################
# Set module settings
#######################

# 18 threads seems a sweet spot
CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 18)
