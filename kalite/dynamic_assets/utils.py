import importlib

from django.conf import settings


def load_dynamic_settings():
    for app in settings.INSTALLED_APPS:
        module_name = '%s.dynamic_settings' % app

        try:
            importlib.import_module(module_name)
        except ImportError:
            continue
