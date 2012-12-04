from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import settings

def require_admin(handler):
    def wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
    return wrapper_fn