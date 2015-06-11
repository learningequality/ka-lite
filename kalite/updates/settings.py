"""





DO NOT MODIFY THIS FILE OR LOAD THIS MODULE.


Because of updates.__init__.py, we cannot load this module independently of its
own child module's preconditions.

I.e. updates.__init__.py expects the django.conf.settings to have loaded, but
updates.settings is a precondition for loading the project's settings module
kalite.settings

Nasty stuff.

Will be cleaned up in 0.14.



"""
import os

try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.auth",  # only admins can access api views
    "django.contrib.staticfiles",
    "south",
    "fle_utils.chronograph",  # updates uses chronograph for commands
    "fle_utils.django_utils",  # templatetags
    # Following line was commented out because it led to distributed app being imported by central server indirectly
    # "kalite.distributed",  # to access caching
    "kalite.i18n",  # language pack updates
    "kalite.main",  # TODO: remove (MainTestCase should be KALiteTestCase)
    "kalite.topic_tools",  # topic tools
    "kalite.testing",
    "securesync",  # Needed to verify zip files (via Device key) and to limit access via registration status
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",  # used by distributed to authenticate admin (django) user
)


#######################
# Set module settings
#######################

CONTENT_ROOT   = os.path.realpath(getattr(local_settings, "CONTENT_ROOT", PROJECT_PATH + "/../content/")) + "/"
CONTENT_URL    = getattr(local_settings, "CONTENT_URL", "/content/")

# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = getattr(local_settings, "BACKUP_VIDEO_SOURCE", None)
BACKUP_THUMBNAIL_SOURCE = getattr(local_settings, "BACKUP_THUMBNAIL_SOURCE", None)

UPDATES_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# settings for when we're updating the server through Git
GIT_UPDATE_REPO_URL    = getattr(local_settings, "GIT_UPDATE_REPO_URL", "https://github.com/learningequality/ka-lite.git")
GIT_UPDATE_BRANCH      = getattr(local_settings, "GIT_UPDATE_BRANCH", "master")
GIT_UPDATE_REMOTE_NAME = getattr(local_settings, "GIT_UPDATE_REMOTE_NAME", "updates")
