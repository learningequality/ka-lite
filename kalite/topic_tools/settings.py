########################
# Django dependencies
########################
import os

INSTALLED_APPS = (
    "kalite.i18n",  # get_video_id
    "kalite.contentload",  # because we have KA path weirdness in our topic tree.  TODO: remove for LEX
    "kalite.testing",
)

#######################
# Set module settings
#######################
DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = getattr(local_settings, "DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP", False)

KHAN_EXERCISES_RELPATH = os.path.join("static", "perseus", "ke")

KHAN_EXERCISES_DIRPATH = os.path.join(os.path.dirname(__file__), "..", KHAN_EXERCISES_RELPATH)
