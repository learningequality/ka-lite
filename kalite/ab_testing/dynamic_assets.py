from django.conf import settings

from .data.groups import get_condition_by_facility_and_unit, get_grade_by_facility
from .data.conditions import CONDITION_SETTINGS

from kalite.student_testing.utils import get_current_unit_settings_value
from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    student_grade_level = fields.IntegerField(default=0)
    unit = fields.IntegerField(default=1)
    is_config_package_nalanda = fields.BooleanField(default="nalanda" in settings.CONFIG_PACKAGE)


# modify ds in-place. Use when you're modifying ds rather than defining new dynamic settings
def modify_dynamic_settings(ds, request=None, user=None):

    user = user or request.session.get('facility_user')

    if user and not user.is_teacher:

        # determine the facility and unit for the current user
        facility = user.facility
        unit = get_current_unit_settings_value(facility.id)

        # look up what condition the user is currently assigned to
        condition = get_condition_by_facility_and_unit(facility, unit)

        # Set grade level on students to enable dynamic checking of student playlists within a unit.
        # TODO (richard): (doge) Much hardcode. Such hack. So get rid. Wow.
        ds["ab_testing"].student_grade_level = get_grade_by_facility(facility)
        ds["ab_testing"].unit = unit
        
        # load the settings associated with the user's current condition
        new_settings = CONDITION_SETTINGS.get(condition, {})

        # merge the settings into the distributed settings (ds) object
        for key, value in new_settings.items():
            namespace, setting = key.split(".")
            if namespace not in ds:
                raise Exception("Could not modify setting '%s': the '%s' app has not defined a dynamic_assets.py file containing DynamicSettings." % (key, namespace))
            if not hasattr(ds[namespace], setting):
                raise Exception("Could not modify setting '%s': no such setting defined in the '%s' app's DynamicSettings." % (key, namespace))
            setattr(ds[namespace], setting, value)
