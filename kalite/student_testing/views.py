from annoying.decorators import render_to

from kalite.shared.decorators import require_login


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
    TODO: Display list of tests for the user.
    """
    context = {}
    return context
