from django.http import HttpResponseRedirect

import settings
from config.models import Settings
from settings import LOG as logging


# TODO(dylan): new class that handles finding and setting the language for the session
class SessionLanguage:
    def process_request(self, request):
        """
        Process requests to set language, redirect to the same URL to continue processing
        without leaving the "set" in the browser history.
        """

        # Set the current language, and redirect (to clean browser history)
        if request.is_admin and request.GET.get("set_default_language"):
            logging.debug("setting default language to %s" % request.GET["set_default_language"])
            Settings.set("default_language", request.GET["set_default_language"])
            return HttpResponseRedirect(request.path)

        elif request.GET.get("set_language"):
            request.session["django_language"] = request.GET["set_language"]
            logging.debug("setting session language to %s" % request.session["django_language"])
            return HttpResponseRedirect(request.path)

        # Process the current language
        if "django_language" not in request.session:
            request.session["django_language"] = Settings.get("default_language") or settings.LANGUAGE_CODE
            logging.debug("setting session language to %s" % request.session["django_language"])

        request.language = request.session["django_language"]
