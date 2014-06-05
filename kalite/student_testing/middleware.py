import logging
import re

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from fle_utils.config.models import Settings


# This must be a string type.
SETTINGS_KEY_EXAM_MODE = 'EXAM_MODE_ON'


class ExamModeCheck:
    """
    If exam-mode is on for the device, redirect user to the exam page set in the exam list page.
    """
    def process_request(self, request):

        # check if logged-in user is a student
        if not request.is_logged_in or request.is_admin or request.is_teacher:
            return None

        # MUST: prevent redirect on certain url patterns
        path = request.path
        url_exceptions = [
            "^/admin/*",
            "^/api/*",
            "^/securesync/*",
            "^/test/*",
            "^/static/*",
            "^/handlebars/*",
        ]
        for item in url_exceptions:
            p = re.compile(item)
            if p.match(path):
                return None

        exam_mode_on = Settings.get(SETTINGS_KEY_EXAM_MODE, '')
        if not exam_mode_on:
            return None

        redirect_to = reverse('test', args=[exam_mode_on])

        # MUST: Redirect to the exam page set in the EXAM_MODE_ON Setting.
        response = HttpResponseRedirect(redirect_to)
        return response