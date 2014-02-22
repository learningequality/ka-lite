"""
This sub-module deals with Zones--how they're defined, permissions related to them,
and the functions to allow joining them.

The "engine" sub-module deals with sharing data within a zone.
"""
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from .models import Device
from utils.internet import set_query_params


def require_registration(resource_name):
    """
    Gets ID of requested user (not necessarily the user logged in)
    """
    def real_decorator(handler):
        def wrapper_fn(request, *args, **kwargs):
            if Device.get_own_device().is_registered():
                return handler(request, *args, **kwargs)
            else:
                messages.warning(request, _("In order to access %(resource_name)s, you must register your device first." % {"resource_name": unicode(resource_name)}))
                return HttpResponseRedirect(
                    set_query_params(reverse('register_public_key'), {'next': request.path})
                );
        return wrapper_fn
    return real_decorator