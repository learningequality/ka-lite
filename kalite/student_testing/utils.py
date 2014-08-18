from django.conf import settings

from fle_utils.config.models import Settings

from .settings import SETTINGS_KEY_EXAM_MODE
from .signals import exam_unset

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

    current_test_id = get_exam_mode_on()
    test_id = getattr(test_object, 'test_id', test_object)
    value = test_id

    # do the import here to prevent circular import
    from .api_resources import Test
    is_test = isinstance(test_object, Test)

    if current_test_id == test_id:
        value = ''
        if is_test and test_object.practice:
            exam_unset.send(sender="None", test_id=current_test_id)

    Settings.set(SETTINGS_KEY_EXAM_MODE, value)

    if is_test:
        return test_object.set_exam_mode()
