import json

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from main.api_forms import AttemptLogForm
from main.api_views import student_log_api
from main.models import AttemptLog

from fle_utils.internet import api_handle_error_with_json, JsonResponse

from .models import TestLog


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
