import simplejson

from main.api_views import student_log_api

from api_forms import TestAttemptLogForm
from models import Test, TestLog, TestAttemptLog

from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from fle_utils.internet import api_handle_error_with_json, JsonResponse

@student_log_api(logged_out_message=_("Exercise progress not saved."))
def save_attempt_log(request):
    """
    Receives an exercise_id and relevant data,
    saves it to the currently authorized user.
    """
    # Form does all data validation, including of the exercise_id
    form = TestAttemptLogForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        raise Exception(form.errors)
    data = form.data

    # More robust extraction of previous object
    user = request.session["facility_user"]

    test = Test.objects.get(pk=data["test"])

    (testlog, was_created) = TestLog.get_or_initialize(user=user, test=test)
    previously_complete = testlog.complete

    testlog.index = data["index"]
    testlog.repeat = data["repeat"]
    testlog.complete = data["complete"]

    try:
        testlog.full_clean()
        testlog.save()
    	TestAttemptLog.objects.create(
    		user=user,
    		test_log=testlog,
    		exercise_id=data["exercise_id"],
    		random_seed=data["random_seed"],
    		)
    except ValidationError as e:
        return JsonResponse({"error": _("Could not save TestAttemptLog") + u": %s" % e}, status=500)
      
    # Special message if you've just completed.
    #   NOTE: it's important to check this AFTER calling save() above.
    if not previously_complete and testlog.complete:
        return JsonResponse({"success": _("You have finished the test!")})

    # Return no message in release mode; "data saved" message in debug mode.
    return JsonResponse({})