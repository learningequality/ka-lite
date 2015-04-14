"""





DO NOT MODIFY THIS FILE OR LOAD THIS MODULE.


Because of i18n.__init__.py, we cannot load this module independently of its
own child module's preconditions.

I.e. i18n.__init__.py expects the django.conf.settings to have loaded, but
i18n.settings is a precondition for loading the project's settings module
kalite.settings

Nasty stuff.

Will be cleaned up in 0.14.



"""
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
