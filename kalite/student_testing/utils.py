from fle_utils.config.models import Settings

from .settings import SETTINGS_KEY_EXAM_MODE

from .signals import exam_unset

def get_exam_mode_on():
    """
    Returns the value of the EXAM_MODE_ON or else return an empty string.
    """
    ret = Settings.get(SETTINGS_KEY_EXAM_MODE, '')
    return ret


def set_exam_mode_on(value):
    """
    Sets the value of the EXAM_MODE_ON.
    TODO(cpauya): check if user is admin/teacher
    """

    current_test_id = get_exam_mode_on()
    if current_test_id == value:
        value = ''
        exam_unset.send(sender=None, test_id=current_test_id)
    return Settings.set(SETTINGS_KEY_EXAM_MODE, value)
