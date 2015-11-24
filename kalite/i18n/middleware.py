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

from .base import get_default_language, set_request_language, select_best_available_language


def set_language_data_from_request(request):
    """
    Process requests to set language, redirect to the same URL to continue processing
    without leaving the "set" in the browser history.
    """
    if "default_language" not in request.session:
        # default_language has the following priority:
        #   facility user's individual setting
        #   config.Settings object's value
        #   settings' value
        request.session["default_language"] = select_best_available_language( \
            getattr(request.session.get("facility_user"), "default_language", None) \
            or get_default_language()
        )

    # Set this request's language based on the listed priority
    cur_lang = (request.GET.get("lang")
                or request.session.get("default_language"))

    set_request_language(request, lang_code=cur_lang)


class SessionLanguage:
    def process_request(self, request):
        request.in_context_localized = settings.IN_CONTEXT_LOCALIZED  # also set whether to turn on in-context localization
        return set_language_data_from_request(request)
