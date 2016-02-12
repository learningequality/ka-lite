"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on API tools from the website, including:
* Getting the overall user status to transform static pages to be user-specific
* Setting the current clock time (RPi)
* Showing the process ID (so that the server can be killed dynamically)
"""
import cgi

from django.contrib.messages.api import get_messages
from django.utils.safestring import SafeString, SafeUnicode

from kalite.main.models import ExerciseLog, VideoLog, ContentLog


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
