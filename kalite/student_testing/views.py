import json
import random

from annoying.decorators import render_to

from kalite.shared.decorators import require_login

from .settings import STUDENT_TESTING_DATA_PATH
from .models import TestLog

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
