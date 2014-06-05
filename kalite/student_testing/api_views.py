import json

from main.api_views import student_log_api

from main.api_forms import AttemptLogForm
from main.models import AttemptLog

from models import TestLog

from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from fle_utils.config.models import Settings
from fle_utils.internet import api_handle_error_with_json, JsonResponse

from kalite.shared.decorators import require_admin

from .middleware import SETTINGS_KEY_EXAM_MODE


@student_log_api(logged_out_message=_("Test progress not saved."))
def save_attempt_log(request):
    """
    Receives an exercise_id and relevant data,
    saves it to the currently authorized user.
    """
    # Form does all data validation, including of the exercise_id
    form = AttemptLogForm(data=json.loads(request.raw_post_data))
    if not form.is_valid():
        raise Exception(form.errors)
    data = form.data

    # More robust extraction of previous object
    user = request.session["facility_user"]

    # test = Test.objects.get(pk=data["test"])

    (testlog, was_created) = TestLog.get_or_initialize(user=user, test=data["title"])
    previously_complete = testlog.complete

    testlog.index = data["index"]
    testlog.complete = data["complete"]

    try:
        testlog.full_clean()
        testlog.save()
        AttemptLog.objects.create(
            user=user,
            exercise_id=data["exercise_id"],
            random_seed=data["random_seed"],
            answer_given=data["answer_given"],
            correct=data["correct"],
            context_type="exam",
            context_id=data["title"]
        )
    except ValidationError as e:
        return JsonResponse({"error": _("Could not save AttemptLog") + u": %s" % e}, status=500)
      
    # Special message if you've just completed.
    #   NOTE: it's important to check this AFTER calling save() above.
    if not previously_complete and testlog.complete:
        return JsonResponse({"success": _("You have finished the test!")})

    # Return no message in release mode; "data saved" message in debug mode.
    return JsonResponse({})

#
# @require_admin
# def set_exam_mode_on(request):
#     """
#     Receives an exam_title and sets it as the Settings.EXAM_MODE_ON value.
#
#     If exam_title are the same on the Settings, means we are disabling it.
#     """
#     try:
#         data = json.loads(request.raw_post_data)
#         exam_title = data['exam_title']
#         # if request.is_ajax and request.is_admin:
#         import logging
#         logging.warn('==> set_exam_mode_on %s' % exam_title)
#         obj, created = Settings.objects.get_or_create(name=SETTINGS_KEY_EXAM_MODE)
#         if obj.value == exam_title:
#             obj.value = ''
#         else:
#             obj.value = exam_title
#         obj.save()
#         return JsonResponse({"success": _("Successfully set the EXAM_MODE_ON setting!")})
#     except Exception as e:
#         return JsonResponse({"error": _("Could not set EXAM_MODE_ON setting.") + u": %s" % e}, status=500)
#     return JsonResponse({"noop": _("Could not set EXAM_MODE_ON setting.")}, status=500)