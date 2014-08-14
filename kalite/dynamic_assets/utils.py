import importlib

from django.conf import settings

from . import models

logging = settings.LOG


def load_dynamic_settings(request, **otherinfo):
    ds = models.DynamicSettings()

    apps = settings.INSTALLED_APPS + settings.DYNAMIC_SETTINGS_PRIORITY_APPS

    for app in apps:
        module_name = '%s.dynamic_settings' % app

        try:
            mod = importlib.import_module(module_name)

            if hasattr(mod, 'define_dynamic_settings'):
                ds += mod.define_dynamic_settings(request, **otherinfo)
            elif hasattr(mod, 'provision_dynamic_settings'):
                mod.provision_dynamic_settings(ds, request, **otherinfo)
        except ImportError:
            continue
        except AttributeError as e:
            logging.warning('Error for module %s: %s' % (module_name, e))
            continue

    return ds
