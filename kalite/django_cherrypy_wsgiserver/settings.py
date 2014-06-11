# Import local settings, for overriding
try:
    import local_settings
except ImportError:
    local_settings = object()

DEBUG = getattr(local_settings, "DEBUG", False)


#######################
# Set module settings
#######################

# 18 threads seems a sweet spot
CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 18)
CHERRPY_PORT = getattr(local_settings, "CHERRYPY_PORT", 8008)

