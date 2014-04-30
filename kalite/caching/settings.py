########################
# Django dependencies
########################

INSTALLED_APPS = (
    'kalite.i18n',  # bad: globally included all apps that have cached vars.
    'kalite.main',  # bad: globally included all apps that have cached vars.
#    'kalite.updates',  # signal listeners on models that affect caches
)
