# Dynamic settings within these apps override settings in all other
# apps. If there are similarly-named settings within the apps below,
# the apps in the end override the earlier defined apps
DYNAMIC_SETTINGS_PRIORITY_APPS = ['kalite.ab_testing']

TEMPLATE_CONTEXT_PROCESSORS = ('kalite.dynamic_assets.custom_context_processors.dynamic_settings', )
