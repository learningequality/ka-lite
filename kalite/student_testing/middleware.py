import re

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from .utils import get_exam_mode_on


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
            "^.*/_generated/*"
        ]
        for item in url_exceptions:
            p = re.compile(item)
            if p.match(path):
                return None

        exam_mode_on = get_exam_mode_on()
        if not exam_mode_on:
            return None

        redirect_to = reverse('test', args=[exam_mode_on])

        # MUST: Redirect to the exam page set in the EXAM_MODE_ON Setting.
        response = HttpResponseRedirect(redirect_to)
        return response
