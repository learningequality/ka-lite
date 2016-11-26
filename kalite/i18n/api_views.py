import json

from django.conf import settings; logging = settings.LOG
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

from .base import get_default_language, set_default_language, set_request_language
from fle_utils.internet.classes import JsonResponse
from fle_utils.internet.decorators import api_handle_error_with_json

@csrf_exempt
@api_handle_error_with_json
def set_server_or_user_default_language(request):
    """This function sets the default language for either the server or user.
    It is accessed via HTTP POST or GET.

    Required Args (POST or GET):
        lang (str): any supported ISO 639-1 language code

    Optional Args (GET):
        returnUrl (str): the URL to redirect the client to after setting the language
        allUsers (bool): when true, set the the default language for all users,
                         when false or missing, set the language for current user

    Returns:
        JSON status, unless a returnUrl is provided, in which case it returns
        a redirect when successful

    Example:
        To set the current user's language to Spanish and send them to
        the Math section, you could use the following link:

            /api/i18n/set_default_language/?lang=es&returnUrl=/learn/khan/math
    """

    returnUrl = ''
    allUsers = ''

    # GET requests are used by RACHEL to jump to a specific page with the
    # language already set so the user doesn't have to.
    if request.method == 'GET':
        data = request.GET
        if not 'lang' in data:
            return redirect('/')
        if 'returnUrl' in data:
            returnUrl = data['returnUrl']
        if 'allUsers' in data:
            allUsers = data['allUsers']
    elif request.method == 'POST':
        data = json.loads(request.raw_post_data) # POST is getting interpreted wrong again by Django

    lang_code = data['lang']

    if allUsers or (request.is_django_user and lang_code != get_default_language()):
        logging.debug("setting server default language to %s" % lang_code)
        set_default_language(lang_code)
    elif not request.is_django_user and request.is_logged_in and lang_code != request.session["facility_user"].default_language:
        logging.debug("setting user default language to %s" % lang_code)
        request.session["facility_user"].default_language = lang_code
        request.session["facility_user"].save()

    if lang_code != request.session.get("default_language"):
        logging.debug("setting session language to %s" % lang_code)
        request.session["default_language"] = lang_code

    set_request_language(request, lang_code)

    if not returnUrl:
        return JsonResponse({"status": "OK"})
    else:
        return redirect(returnUrl)
