"""
i18n/middleware:

THIS IS FOR THE DISTRIBUTED SERVER ONLY

Here, we have three major pieces of code:
1. Set the language for the request (request.session["django_language"], copied to request.language),
  using some cached data (see code below) or the "lang" GET parameter
2. (optional) Set the language for this user (facility users only) via "set_user_language" GET parameter
3. (optional) Set the default language for this installation (teacher or superuser rights required)
  via the "set_server_language" GET parameter

Other values set here:
  request.session["default_language"] - if no "lang" GET parameter is specified, this is the language to use on the current request.
  request.session["language_choices"] - available languages (based on language pack metadata)
  request.session["django_language"] - (via settings.LANGUAGE_COOKIE_NAME) used by Django, it's what it uses as the request language.
  request.language - proxy for request.session["django_language"] / request.session[settings.LANGUAGE_COOKIE_NAME]
"""
from django.conf import settings; logging = settings.LOG
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from . import get_default_language, get_installed_language_packs, lcode_to_django_lang, lcode_to_ietf, select_best_available_language, set_default_language
from fle_utils.config.models import Settings
from fle_utils.internet import set_query_params


def set_default_language_from_request(request, lang_code, global_set=False):
    """
    global_set has different meanings for different users.
    For students, it means their personal default language
    For teachers, it means their personal default language
    For django users, it means the server language.
    """

    # Get lang packs directly, to force reloading, as they may have changed.
    lang_packs = get_installed_language_packs(force=True).keys()
    lang_code = select_best_available_language(lang_code, available_codes=lang_packs)  # Make sure to reload available languages; output is in django_lang format

    if lang_code != request.session.get("default_language"):
        logging.debug("setting session language to %s" % lang_code)
        request.session["default_language"] = lang_code

    if global_set:
        if request.is_django_user and lang_code != get_default_language():
            logging.debug("setting server default language to %s" % lang_code)
            set_default_language(lang_code)
        elif not request.is_django_user and request.is_logged_in and lang_code != request.session["facility_user"].default_language:
            logging.debug("setting user default language to %s" % lang_code)
            request.session["facility_user"].default_language = lang_code
            request.session["facility_user"].save()

    set_request_language(request, lang_code)


def set_request_language(request, lang_code):
    # each request can get the language from the querystring, or from the currently set session language

    lang_code = select_best_available_language(lang_code)  # output is in django_lang format

    if lang_code != request.session.get(settings.LANGUAGE_COOKIE_NAME):
        logging.debug("setting request language to %s (session language %s), from %s" % (lang_code, request.session.get("default_language"), request.session.get(settings.LANGUAGE_COOKIE_NAME)))
        # Just in case we have a db-backed session, don't write unless we have to.
        request.session[settings.LANGUAGE_COOKIE_NAME] = lang_code

    request.language = lcode_to_ietf(lang_code)
    translation.activate(request.language)


def set_language_data_from_request(request):
    """
    Process requests to set language, redirect to the same URL to continue processing
    without leaving the "set" in the browser history.
    """
    if "set_server_language" in request.GET:
        # Set the current server default language, and redirect (to clean browser history)
        if not request.is_admin:
            raise PermissionDenied(_("You don't have permissions to set the server's default language."))

        set_default_language_from_request(request, lang_code=request.GET["set_server_language"], global_set=True)

        # Redirect to the same URL, but without the GET param,
        #   to remove the language setting from the browser history.
        redirect_url = set_query_params(request.get_full_path(), {"set_server_language": None})
        return HttpResponseRedirect(redirect_url)

    elif "set_user_language" in request.GET:
        # Set the current user's session language, and redirect (to clean browser history)
        set_default_language_from_request(request, request.GET["set_user_language"], global_set=(request.is_logged_in and not request.is_django_user))

        # Redirect to the same URL, but without the GET param,
        #   to remove the language setting from the browser history.
        redirect_url = set_query_params(request.get_full_path(), {"set_user_language": None})
        return HttpResponseRedirect(redirect_url)

    if not "default_language" in request.session:
        # default_language has the following priority:
        #   facility user's individual setting
        #   config.Settings object's value
        #   settings' value
        request.session["default_language"] = select_best_available_language( \
            getattr(request.session.get("facility_user"), "default_language", None) \
            or get_default_language()
        )

    # Set this request's language based on the listed priority
    cur_lang = request.GET.get("lang") \
        or request.session.get("default_language")

    set_request_language(request, lang_code=cur_lang)


class SessionLanguage:
    def process_request(self, request):
        return set_language_data_from_request(request)
