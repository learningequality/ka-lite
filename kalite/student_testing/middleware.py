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

        if not request.is_logged_in:
            return None

        exam_mode_on = Settings.get(SETTINGS_KEY_EXAM_MODE, False)
        # print '==> EXAM_MODE_ON', exam_mode_on
        if not exam_mode_on:
            return None

        # print '====> process_request', request.user, request.is_admin, request.path

        # TODO: How to check if logged-in user is a student?
        if request.is_admin or request.is_teacher:
            return None

        # MUST: prevent redirect on certain url patterns
        path = request.path
        redirect_to = reverse("account_management")
        url_exceptions = [
            "^/api/*",
            "^/securesync/*",
            redirect_to
        ]
        for item in url_exceptions:
            p = re.compile(item)
            # print '====> trying url ignore pattern', item, 'redirect_to==', redirect_to, p.match(redirect_to)
            if p.match(path):
                # print '======> url ignore match', item
                return None

        # print '====> redirecting to', redirect_to, 'from', request.path

        # TODO: Redirect to the exam page set in the exam list page, for now, just redirect to user profile page.
        response = HttpResponseRedirect(redirect_to)
        return response