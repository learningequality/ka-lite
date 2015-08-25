from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from .models import Device
from fle_utils.internet.functions import set_query_params, am_i_online


def require_registration(resource_name):
    """
    Gets ID of requested user (not necessarily the user logged in)
    """
    def real_decorator_wrapper(handler):
        def real_decorator_wrapper_fn(request, *args, **kwargs):
            if Device.get_own_device().is_registered() or not am_i_online(settings.CENTRAL_SERVER_URL):
                return handler(request, *args, **kwargs)
            else:
                messages.warning(
                    request,
                    _("In order to access %(resource_name)s, you must register your device first."
                      % {"resource_name": unicode(resource_name)})
                )
                return HttpResponseRedirect(
                    set_query_params(reverse('register_public_key'), {'next': request.path})
                )
        return real_decorator_wrapper_fn
    return real_decorator_wrapper
