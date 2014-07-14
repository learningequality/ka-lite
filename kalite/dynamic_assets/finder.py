import importlib
import itertools
import string
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, DatabaseError

logging = settings.LOG

def _dynamic_settings(appname):
    module_name = '%s.dynamic_settings' % appname

    try:
        module = importlib.import_module(module_name)
        setting = getattr(module, 'DynamicSettings')

        # if it's a db model, return an instance so callees don't have
        # to muck around with fetching it. Take note though that
        # callees are responsible for calling .save()
        if models.Model not in setting.mro():
            return setting
        else:
            # hmm double nested try clause... not sure if this is
            # idiomatic.
            try:
                return setting.objects.get()
            except ObjectDoesNotExist:
                return setting()
            except DatabaseError as e:
                logging.warning("Skipping %s because of db error: %s" % (setting.__module__, e))
                return None
    except ImportError:
        return None


def _discover_all_dynamic_settings(applist=None):
    if not applist:
        applist = settings.INSTALLED_APPS


    for app in applist:
        s = _dynamic_settings(app)
        if s:
            yield s


def all_dynamic_settings():
    '''
    Build a dictionary containing settings stored in each app's setting
    app.
    '''

    result = dict()
    all_settings = set(_discover_all_dynamic_settings())
    priority_settings = set(_discover_all_dynamic_settings(applist=settings.DYNAMIC_SETTINGS_PRIORITY_APPS))

    # remove settings defined in DYNAMIC_SETTINGS_PRIORITY_APPS,
    # to make sure they're not double applied
    all_settings -= priority_settings

    for setting in itertools.chain(all_settings, priority_settings):
        for attr, val in setting.__dict__.iteritems():
            # a setting is supposed to be an attribute with all
            # uppercase letters, but since i'm lazy we just check the
            # first letter and use that as heuristic
            if attr[0] in string.ascii_uppercase:
                result[attr] = val

    return result
