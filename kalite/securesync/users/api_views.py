import cgi
import json
import re
import uuid

from django.core import serializers
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.db import models as db_models
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

import settings
import version
from .models import *
from config.models import Settings
from main.models import VideoLog, ExerciseLog, VideoFile
from shared import serializers
from utils.decorators import distributed_server_only, allow_jsonp, api_handle_error_with_json
from utils.internet import JsonResponse, am_i_online


# On pages with no forms, we want to ensure that the CSRF cookie is set, so that AJAX POST
# requests will be possible. Since `status` is always loaded, it's a good place for this.
@ensure_csrf_cookie
@distributed_server_only
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
    message_dicts = []
    for message in get_messages(request):
        # Make sure to escape strings not marked as safe.
        # Note: this duplicates a bit of Django template logic.
        msg_txt = message.message
        if not (isinstance(msg_txt, SafeString) or isinstance(msg_txt, SafeUnicode)):
            msg_txt = cgi.escape(str(msg_txt))

        message_dicts.append({
            "tags": message.tags,
            "text": msg_txt,
        })

    # Default data
    data = {
        "is_logged_in": request.is_logged_in,
        "registered": bool(Settings.get("registered")),
        "is_admin": request.is_admin,
        "is_django_user": request.is_django_user,
        "points": 0,
        "messages": message_dicts,
    }
    # Override properties using facility data
    if "facility_user" in request.session:
        user = request.session["facility_user"]
        data["is_logged_in"] = True
        data["username"] = user.get_name()
        data["points"] = VideoLog.get_points_for_user(user) + ExerciseLog.get_points_for_user(user)
    # Override data using django data
    if request.user.is_authenticated():
        data["is_logged_in"] = True
        data["username"] = request.user.username

    return JsonResponse(data)

