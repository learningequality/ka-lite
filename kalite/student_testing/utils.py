from django.conf import settings

from fle_utils.config.models import Settings

from .settings import SETTINGS_KEY_EXAM_MODE
from kalite.student_testing.signals import exam_unset

logging = settings.LOG


def get_exam_mode_on():
    """
    Returns the value of the EXAM_MODE_ON or else return an empty string.
    """
    ret = Settings.get(SETTINGS_KEY_EXAM_MODE, '')
    return ret


def set_exam_mode_on(test_object):
    """
    Sets the value of the EXAM_MODE_ON.
    TODO(cpauya): check if user is admin/teacher
    """

    # Figure out what the previous exam was, and then turn off exam mode
    # (to make sure we trigger any exam unsetting events)
    old_test_id = get_exam_mode_on()
    set_exam_mode_off()

    new_test_id = getattr(test_object, 'test_id', test_object)

    # only enable exam if it isn't the same one previously enabled
    # (since we for some reason just call the same method to toggle off)
    if old_test_id != new_test_id:
        Settings.set(SETTINGS_KEY_EXAM_MODE, new_test_id)


def set_exam_mode_off():
    """Switch off exam mode if it is on, do nothing if already off"""

    current_test_id = get_exam_mode_on()
    if not current_test_id:
        return

    # do the import here to prevent circular import
    from .models import Test

    test = Test.all().get(current_test_id, None)

    if test and test.practice:
        exam_unset.send(sender="None", test_id=current_test_id)

    Settings.set(SETTINGS_KEY_EXAM_MODE, '')

    return

# ==========================
# Some constants and helper functions to be used for the "Current Unit" feature.
# ==========================

SETTINGS_FACILITY_ID_CHARS = 8