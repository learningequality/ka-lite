"""





DO NOT MODIFY THIS FILE OR LOAD THIS MODULE.


Because of caching.__init__.py, we cannot load this module independently of its
own child module's preconditions.

I.e. caching.__init__.py expects the django.conf.settings to have loaded, but
caching.settings is a precondition for loading the project's settings module
kalite.settings

Nasty stuff.

Will be cleaned up in 0.14.



"""
########################
# Django dependencies
########################

INSTALLED_APPS = (
    'kalite.i18n',  # bad: globally included all apps that have cached vars.
    'kalite.testing',  # KALiteTestCase
    'kalite.topic_tools',  # bad: globally included all apps that have cached vars.
    'kalite.updates',
)
