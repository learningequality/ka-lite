########################
# Django dependencies
########################

INSTALLED_APPS = (
    "kalite.i18n",  # get_video_id
    "kalite.contentload",  # because we have KA path weirdness in our topic tree.  TODO: remove for LEX
    "kalite.testing",
)

#######################
# Set module settings
#######################
DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = getattr(local_settings, "DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP", False)