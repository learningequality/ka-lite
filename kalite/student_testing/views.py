from annoying.decorators import render_to

from shared.topic_tools import get_topic_exercises
from models import Test

@render_to("student_testing/test.html")
def test(request, test_id):
    """
    Display a test
    """

    test_item = Test.objects.get(pk=test_id)
    path = getattr(test_item, "path")

    context = {
        "test": test_item,
    }
    return context