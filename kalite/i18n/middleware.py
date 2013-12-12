from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

import settings
from .models import LanguagePack
from config.models import Settings
from settings import LOG as logging
from shared.i18n import lcode_to_django_lang, lcode_to_ietf


class SessionLanguage:
    def set_default_language(self, request, lang_code, global_set=False):
        lang_code = lcode_to_django_lang(lang_code)

        if lang_code != request.session.get("default_language"):
            logging.debug("setting session language to %s" % lang_code)
            request.session["default_language"] = lang_code
        if global_set:
            if not request.is_admin:
                raise PermissionDenied(_("You don't have permissions to set the server's default language."))
            if lang_code != Settings.get("default_language"):
                logging.debug("setting default language to %s" % lang_code)
                Settings.set("default_language", lang_code)
        self.set_request_language(request, lang_code)

    def set_request_language(self, request, lang_code):
        # each request can get the language from the querystring, or from the currently set session language

        lang_code = lcode_to_django_lang(lang_code)
        if lang_code != request.session.get("django_language"):
            logging.debug("setting session language to %s" % lang_code)
            # Just in case we have a db-backed session, don't write unless we have to.
            request.session["django_language"] = lang_code

        request.language = lcode_to_ietf(lang_code)

    def process_request(self, request):
        """
        Process requests to set language, redirect to the same URL to continue processing
        without leaving the "set" in the browser history.
        """

        if "language_choices" not in request.session:
            # Set the set of available languages
            request.session["language_choices"] = list(LanguagePack.objects.all())

        if "set_default_language" in request.GET:
            # Set the current server default language, and redirect (to clean browser history)
            if not request.is_admin:
                raise PermissionDenied(_("You don't have permissions to set the server's default language."))

            self.set_default_language(request, lang_code=request.GET["set_default_language"], global_set=True)

            redirect_url = request.get_full_path().replace("set_default_language="+request.GET["set_default_language"], "")
            return HttpResponseRedirect(redirect_url)

        elif "set_language" in request.GET:
            # Set the current user's session language, and redirect (to clean browser history)
            self.set_default_language(request, request.GET["set_language"])

            redirect_url = request.get_full_path().replace("set_language="+request.GET["set_language"], "")
            return HttpResponseRedirect(redirect_url)

        if not "default_language" in request.session:
            request.session["default_language"] = Settings.get("default_language") or settings.LANGUAGE_CODE

        # Set this request's language based on the listed priority
        cur_lang = request.GET.get("lang") \
            or request.session.get("django_language") \
            or request.session.get("default_language")
        self.set_request_language(request, lang_code=cur_lang)
