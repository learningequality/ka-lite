from django.http import HttpResponseRedirect

import settings
from config.models import Settings
from settings import LOG as logging


class GetNextParam:
    def process_request(self, request):
        next = request.GET.get("next", "")
        if next.startswith("/"):    
            request.next = next
        else:
            request.next = ""


# TODO(dylan): new class that handles finding and setting the language for the session
class SessionLanguage:
    def process_request(self, request):
        """
        Process requests to set language, redirect to the same URL to continue processing
        without leaving the "set" in the browser history.
        """
        if request.is_admin and request.GET.get("set_default_language"):
            Settings.set("default_language", request.GET.get("set_default_language"))
            return HttpResponseRedirect(request.path)
        elif request.GET.get("set_language"):
            request.session["django_language"] = request.GET.get("set_language")
            return HttpResponseRedirect(request.path)
        else:
            request.session["django_language"] = Settings.get("default_language") or settings.LANGUAGE_CODE

        request.language = request.session["django_language"]
