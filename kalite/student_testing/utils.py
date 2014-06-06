from fle_utils.config.models import Settings

from .settings import SETTINGS_KEY_EXAM_MODE


def get_exam_mode_on():
    """
    Returns the value of the EXAM_MODE_ON or else return an empty string.
    """
    ret = Settings.get(SETTINGS_KEY_EXAM_MODE, '')
    return ret