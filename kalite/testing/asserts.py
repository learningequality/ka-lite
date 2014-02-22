from django.http import Http404

import settings


def central_server_only(handler):
    """
    Assert-like decorator that marks a function for use only on the central server.
    """
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            raise Http404(_("This path is only available on the central server."))
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    """
    Assert-like decorator that marks a function for use only on a distributed server.
    """
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            raise Http404(_("This path is only available on distributed servers."))
        return handler(*args, **kwargs)
    return wrapper_fn
