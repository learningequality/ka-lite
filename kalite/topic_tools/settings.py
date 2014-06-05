########################
# Django dependencies
########################

INSTALLED_APPS = (
    "kalite.i18n",  # get_video_id
    "kalite.khanload",  # because we have KA path weirdness in our topic tree.  TODO: remove for LEX
    "kalite.testing",
)

#######################
# Set module settings
#######################

TOPICS_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
