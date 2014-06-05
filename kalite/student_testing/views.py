from django.core.exceptions import PermissionDenied

from annoying.decorators import render_to

from kalite.shared.decorators import require_login, require_admin


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


@require_admin
@render_to("student_testing/test_list.html")
def test_list(request):
    """
    Display list of tests for the admin user like the teacher.
    """
    context = {}
    return context
