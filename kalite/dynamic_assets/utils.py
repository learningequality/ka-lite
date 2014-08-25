import importlib

from django.conf import settings

logging = settings.LOG


def load_dynamic_settings(request=None, user=None):

    # load all the "dynamic_assets.py" files present in installed apps
    modules = []
    for app in settings.INSTALLED_APPS:
        try:
            modules.append((app.split(".")[-1], importlib.import_module('%s.dynamic_assets' % app)))
        except ImportError:
            pass

    ds = {}

    # in the first pass, load all app-specific dynamic settings
    for key, mod in modules:

        if hasattr(mod, "DynamicSettings"):
            ds[key] = mod.DynamicSettings()

    # in the second pass, run the accumulated dynamic settings object through any middleware
    if request or user:
        for key, mod in modules:
            if hasattr(mod, "modify_dynamic_settings"):
                mod.modify_dynamic_settings(ds, request=request, user=user)

    return ds
