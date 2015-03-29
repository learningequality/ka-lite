"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on API tools from the website, including:
* Getting the overall user status to transform static pages to be user-specific
* Setting the current clock time (RPi)
* Showing the process ID (so that the server can be killed dynamically)
"""
import cgi
import os
import datetime

from django.conf import settings
from django.contrib.messages.api import get_messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie

from .api_forms import DateTimeForm
from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError
from fle_utils.testing.decorators import allow_api_profiling
from kalite import version
from kalite.main.models import ExerciseLog, VideoLog, ContentLog
from kalite.shared.decorators.auth import require_admin



@require_admin
@api_handle_error_with_json
def time_set(request):
    """
    Receives a date-time string and sets the system date-time
    RPi only.
    """

    if not settings.ENABLE_CLOCK_SET:
        return JsonResponseMessageError(_("Time reset can only be done on Raspberry Pi systems."), status=403)

    # Form does all the data validation - including ensuring that the data passed is a proper date time.
    # This is necessary to prevent arbitrary code being run on the system.
    form = DateTimeForm(data=simplejson.loads(request.body))
    if not form.is_valid():
        return JsonResponseMessageError(_("Could not read date and time: Unrecognized input data format."), status=400)

    try:

        if os.system('sudo date +%%F%%T -s "%s"' % form.data["date_time"]):
            raise PermissionDenied

    except PermissionDenied as e:
        return JsonResponseMessageError(
            _("System permissions prevented time setting, please run with root permissions."), status=500)

    now = datetime.datetime.now().isoformat(" ").split(".")[0]

    return JsonResponseMessage(_("System time was reset successfully."))


# Functions below here focused on users


def compute_total_points(user):
    if user.is_teacher:
        return None
    else:
        return (VideoLog.get_points_for_user(user) +
                ExerciseLog.get_points_for_user(user) +
                ContentLog.get_points_for_user(user))


def get_messages_for_api_calls(request):
    """
    Re-usable function that returns a list of messages to be used by API calls.
    """
    message_lists = []
    for message in get_messages(request):
        # Make sure to escape strings not marked as safe.
        # Note: this duplicates a bit of Django template logic.
        msg_txt = message.message
        if not (isinstance(msg_txt, SafeString) or isinstance(msg_txt, SafeUnicode)):
            msg_txt = cgi.escape(unicode(msg_txt))
        msg_type = message.tags
        message_lists.append({msg_type: msg_txt})
    return message_lists
