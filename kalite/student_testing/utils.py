from django.conf import settings

from fle_utils.config.models import Settings

from .settings import SETTINGS_KEY_EXAM_MODE
from kalite.playlist import UNITS
from kalite.student_testing.signals import exam_unset, unit_switch

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

SETTINGS_CURRENT_UNIT_PREFIX = 'current_unit_'
SETTINGS_FACILITY_ID_CHARS = 8

def get_current_unit_settings_name(facility_id):
    name = SETTINGS_CURRENT_UNIT_PREFIX
    if facility_id:
        name = "%s%s" % (name, facility_id[:SETTINGS_FACILITY_ID_CHARS],)
    return name


def set_current_unit_settings_value(facility_id, value):
    """
    Set the value of the current unit on Settings based on the facility id.
    """
    old_unit = get_current_unit_settings_value(facility_id)
    name = get_current_unit_settings_name(facility_id)
    s = Settings.set(name, value)
    unit_switch.send(sender="None", old_unit=old_unit, new_unit=value, facility_id=facility_id)
    return s


def get_current_unit_settings_value(facility_id):
    """
    Get value of current unit based on facility id.  If none, defaults to 1 and creates an
    entry on the Settings.
    """
    name = get_current_unit_settings_name(facility_id)
    value = Settings.get(name, UNITS[0])
    if value == 0:
        # This may be the first time this facility`s current unit is queried so
        # make sure it has a value at Settings so we can either change it on
        # the admin page or at front-end code later.
        value = 1
        Settings.set(name, value)
    return value
