"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on API tools from the website, including:
* Getting the overall user status to transform static pages to be user-specific
* Setting the current clock time (RPi)
* Showing the process ID (so that the server can be killed dynamically)
"""
import cgi
import copy
import json
import os
import re
import os
import datetime
from annoying.functions import get_object_or_None
from functools import partial

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

from .api_forms import DateTimeForm
from fle_utils.config.models import Settings
from fle_utils.general import break_into_chunks
from fle_utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessage, \
    JsonResponseMessageError, JsonResponseMessageWarning
from fle_utils.orderedset import OrderedSet
from fle_utils.testing.decorators import allow_api_profiling
from kalite import version
from kalite.facility.models import FacilityGroup, FacilityUser
from kalite.i18n import lcode_to_ietf
from kalite.main.models import ExerciseLog, VideoLog, ContentLog
from kalite.shared.decorators import require_admin


@require_admin
@api_handle_error_with_json
def time_set(request):
    """
    Receives a date-time string and sets the system date-time
    RPi only.
    """

    if not settings.ENABLE_CLOCK_SET:
        return JsonResponseMessageError(_("Time reset can only be done on Raspberry Pi systems."))

    # Form does all the data validation - including ensuring that the data passed is a proper date time.
    # This is necessary to prevent arbitrary code being run on the system.
    form = DateTimeForm(data=simplejson.loads(request.body))
    if not form.is_valid():
        return JsonResponseMessageError(_("Could not read date and time: Unrecognized input data format."))

    try:

        if os.system('sudo date +%%F%%T -s "%s"' % form.data["date_time"]):
            raise PermissionDenied

    except PermissionDenied as e:
        return JsonResponseMessageError(
            _("System permissions prevented time setting, please run with root permissions."))

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


# On pages with no forms, we want to ensure that the CSRF cookie is set, so that AJAX POST
# requests will be possible. Since `status` is always loaded, it's a good place for this.
@ensure_csrf_cookie
@allow_api_profiling
@api_handle_error_with_json
def status(request):
    """In order to promote (efficient) caching on (low-powered)
    distributed devices, we do not include ANY user data in our
    templates.  Instead, an AJAX request is made to download user
    data, and javascript used to update the page.

    This view is the view providing the json blob of user information,
    for each page view on the distributed server.

    Besides basic user data, we also provide access to the
    Django message system through this API, again to promote
    caching by excluding any dynamic information from the server-generated
    templates.
    """
    # Build a list of messages to pass to the user.
    #   Iterating over the messages removes them from the
    #   session storage, thus they only appear once.

    message_dicts = get_messages_for_api_calls(request)

    # Default data
    data = {
        "is_logged_in": request.is_logged_in,
        "registered": request.session.get("registered", True),
        "is_admin": request.is_admin,
        "is_django_user": request.is_django_user,
        "points": 0,
        "current_language": request.session[settings.LANGUAGE_COOKIE_NAME],
        "messages": message_dicts,
        "status_timestamp": datetime.datetime.now(),
        "version": version.VERSION,
    }

    # Override properties using facility data
    if "facility_user" in request.session:  # Facility user
        user = request.session["facility_user"]
        data["is_logged_in"] = True
        data["username"] = user.get_name()
        # TODO-BLOCKER(jamalex): re-enable this conditional once tastypie endpoints invalidate cached session value
        # if "points" not in request.session:
        request.session["points"] = compute_total_points(user)
        data["points"] = request.session["points"] if request.session["points"] else 0
        data["user_id"] = user.id
        data["user_uri"] = reverse("api_dispatch_detail", kwargs={"resource_name": "user", "pk": user.id})
        data["facility_id"] = user.facility.id

    # Override data using django data
    if request.user.is_authenticated():  # Django user
        data["is_logged_in"] = True
        data["username"] = request.user.username

    return JsonResponse(data)
