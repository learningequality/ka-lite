from django.http.response import Http404

from annoying.decorators import render_to

from kalite.shared.decorators.auth import require_login, require_admin

from .utils import get_exam_mode_on


@require_login
@render_to("student_testing/test.html")
def test(request, test_id):
    """
    Display a test when it is on exam-mode at Settings only when exam-mode is on for the test.
    Do the filter if the user is not an admin.
    """
    if not request.is_admin and test_id != get_exam_mode_on():
        raise Http404()

    context = {
        "test_id": test_id,
    }
    return context


@require_admin
@render_to("student_testing/test_list.html")
def test_list(request):
    """
    Display list of tests for the admin user like the teacher.
    """
    context = {}
    return context


@require_admin
@render_to("student_testing/current_unit.html")
def current_unit(request):
    """
    Display list of facilities with the current unit column accessible only for the admin user like the teacher.
    """
    context = {}
    return context
