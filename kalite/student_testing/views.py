import json
import random

from annoying.decorators import render_to

from kalite.main.topic_tools import get_topic_exercises

from kalite.shared.decorators import require_login

from .settings import STUDENT_TESTING_DATA_PATH
from .models import TestLog

@require_login
@render_to("student_testing/test.html")
def test(request, test_id):
    """
    Display a test
    """

    test_item = json.load(open(STUDENT_TESTING_DATA_PATH + "/" + test_id + ".json", "r"))

    was_created = False

    preview = False

    if request.user.is_superuser:
        preview = True

    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        # test_item = Test.objects.get(pk=test_id)

        test_item = json.load(open(STUDENT_TESTING_DATA_PATH + "/" + test_id + ".json", "r"))

        (testlog, was_created) = TestLog.get_or_initialize(user=user, test=test_item["title"])

    if was_created or preview:
        ids = test_item["ids"]
        seeds = range(test_item["seed"], test_item["seed"] + test_item["repeats"])
        id_blocks = {}
        for exercise_id in ids:
            id_blocks[exercise_id] = [list(zipped) for zipped in zip([str(exercise_id)]*test_item["repeats"], seeds)]
            random.shuffle(id_blocks[exercise_id])
        test_sequence = json.dumps([id_blocks[exercise_id][i] for i,seed in enumerate(seeds) for exercise_id in ids])
        if not preview:
            testlog.test_sequence = test_sequence
            testlog.save()
    try:
        test_sequence = testlog.test_sequence
        index = testlog.index
        complete = testlog.complete
    except NameError:
        index = 0
        complete = False

    item_sequence = json.dumps([item[0] for item in json.loads(test_sequence)])
    seed_sequence = json.dumps([item[1] for item in json.loads(test_sequence)])
    context = {
        "item_sequence": item_sequence,
        "seed_sequence": seed_sequence,
        "test": test_item["title"],
        "index": index,
        "complete": complete,
    }
    return context