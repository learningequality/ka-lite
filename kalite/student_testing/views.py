from annoying.decorators import render_to

from kalite.main.topic_tools import get_topic_exercises

from models import Test, TestLog

@render_to("student_testing/test.html")
def test(request, test_id):
    """
    Display a test
    """
    user = request.session["facility_user"]
    test_item = Test.objects.get(pk=test_id)
    path = getattr(test_item, "path")
    (testlog, was_created) = TestLog.get_or_initialize(user=user, test=test_item)

    context = {
        "index": testlog.index,
        "repeat": testlog.repeat,
        "test": test_item,
    }
    return context