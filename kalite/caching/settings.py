########################
# Django dependencies
########################

INSTALLED_APPS = (
    'kalite.i18n',  # bad: globally included all apps that have cached vars.
    'kalite.testing',  # KALiteTestCase
    'kalite.topic_tools',  # bad: globally included all apps that have cached vars.
    'kalite.updates',
)
