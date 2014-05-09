import json
import random

from annoying.decorators import render_to

from kalite.main.topic_tools import get_topic_exercises
from kalite.student_testing.settings import STUDENT_TESTING_DATA_PATH

from kalite.shared.decorators import require_login

from models import TestLog#, Test

@require_login
@render_to("student_testing/test.html")
def test(request, test_id):
    """
    Display a test
    """
    user = request.session["facility_user"]
    # test_item = Test.objects.get(pk=test_id)

    test_item = json.load(open(STUDENT_TESTING_DATA_PATH + "/" + test_id + ".json", "r"))

    (testlog, was_created) = TestLog.get_or_initialize(user=user, test=test_item["title"])

    if was_created or not testlog.test_sequence:
        ids = test_item["ids"]
        seeds = range(test_item["seed"], test_item["seed"] + test_item["repeats"])
        id_blocks = {}
        for exercise_id in ids:
            id_blocks[exercise_id] = [list(zipped) for zipped in zip([exercise_id]*test_item.repeats, seeds)]
            random.shuffle(id_blocks[exercise_id])
        test_sequence = [id_blocks[exercise_id][i] for i,seed in enumerate(seeds) for exercise_id in ids]
        testlog.test_sequence = test_sequence
        testlog.save()

    context = {
        "test_sequence": testlog.test_sequence,
        "test": test_item,
        "index": testlog.index,
        "complete": testlog.complete,
    }
    return context