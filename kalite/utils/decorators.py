from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
import settings

def require_admin(handler):
    def wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)
        messages.error(request, mark_safe("To view the page you were trying to view, you need to be logged in as a " +
            "teacher or an admin. Please login as one below, or <a href='%s'>go to home</a>." % reverse("homepage")))
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
    return wrapper_fn