from django.core.exceptions import PermissionDenied

from annoying.decorators import render_to

from fle_utils.config.models import Settings

from kalite.shared.decorators import require_login

from .middleware import SETTINGS_KEY_EXAM_MODE


@require_login
@render_to("student_testing/test.html")
def test(request, test_title):
    """
    Display a test
    """
    context = {
        "title": test_title,
    }
    return context


@require_login
@render_to("student_testing/test_list.html")
def test_list(request):
    """
    Display list of tests for the teacher.
    """
    if not request.is_admin:
        raise PermissionDenied

    exam_mode_on = Settings.get(SETTINGS_KEY_EXAM_MODE, '')
    context = {
        'exam_mode_on': exam_mode_on
    }
    return context
