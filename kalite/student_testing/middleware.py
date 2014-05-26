import re

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from fle_utils.config.models import Settings


SETTINGS_KEY_EXAM_MODE = 'EXAM_MODE_ON'


class ExamModeCheck:
    """
    If exam-mode is on for the device, redirect user to the exam page set in the exam list page.
    """
    def process_request(self, request):

        # MUST: prevent redirect on certain url patterns
        path = request.path
        redirect_to = reverse("account_management")
        url_exceptions = [
            "^/admin/*",
            "^/api/*",
            "^/securesync/*",
            redirect_to
        ]
        for item in url_exceptions:
            p = re.compile(item)
            if p.match(path):
                return None

        # check if logged-in user is a student
        if not request.is_logged_in or request.is_admin or request.is_teacher:
            return None

        exam_mode_on = Settings.get(SETTINGS_KEY_EXAM_MODE, False)
        if not exam_mode_on:
            return None

        # TODO: Redirect to the exam page set in the exam list page, for now, just redirect to user profile page.
        response = HttpResponseRedirect(redirect_to)
        return response