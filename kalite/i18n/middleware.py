from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

import settings
from .models import LanguagePack
from config.models import Settings
from settings import LOG as logging
from shared.i18n import lcode_to_django_lang, lcode_to_ietf


class SessionLanguage:
    def set_language(self, request, cur_lang):
        # each request can get the language from the querystring, or from the currently set session language
        old_lang = request.session.get("django_language", "")
        if cur_lang != old_lang:
            logging.debug("setting session language to %s" % cur_lang)

        # Set the two variables we care most about
        request.session["django_language"] = cur_lang
        request.session["default_language"] = cur_lang
        request.language = lcode_to_ietf(cur_lang)

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

            lang_code = lcode_to_django_lang(request.GET["set_default_language"])

            self.set_language(request, lang_code)
            Settings.set("default_language", lang_code)
            logging.debug("setting default language to %s" % lang_code)

            redirect_url = request.get_full_path().replace("set_default_language="+request.GET["set_default_language"], "")
            return HttpResponseRedirect(redirect_url)

        elif "set_language" in request.GET:
            # Set the current user's session language, and redirect (to clean browser history)
            lang_code = lcode_to_django_lang(request.GET["set_language"])

            self.set_language(request, lang_code)
            logging.debug("setting session language to %s" % lang_code)

            redirect_url = request.get_full_path().replace("set_language="+request.GET["set_language"], "")
            return HttpResponseRedirect(redirect_url)

        # Set this request's language based on the listed priority
        cur_lang = lcode_to_django_lang( \
            request.GET.get("lang") \
            or request.session.get("django_language") \
            or request.session.get("default_language") \
            or settings.LANGUAGE_CODE \
        )
        self.set_language(request, cur_lang)
