"""

benjaoming:

This file replaces caching.settings temporarily until caching.__init__.py has been
cleaned up to not contain references to django post-load modules.


DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY


This will be cleaned up in KA Lite 0.14


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
