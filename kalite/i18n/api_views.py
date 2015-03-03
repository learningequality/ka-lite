import json

from django.conf import settings; logging = settings.LOG
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from . import get_default_language, set_default_language, set_request_language
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError
from fle_utils.internet.decorators import api_handle_error_with_json


@csrf_exempt
@api_handle_error_with_json
def set_server_or_user_default_language(request):
    if request.method == 'GET':
        return JsonResponseMessageError(_("Can only handle default language changes through POST requests"), status=405)

    elif request.method == 'POST':
        data = json.loads(request.raw_post_data) # POST is getting interpreted wrong again by Django
        lang_code = data['lang']

        if request.is_django_user and lang_code != get_default_language():
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

        return JsonResponse({"status": "OK"})
