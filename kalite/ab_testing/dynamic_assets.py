from .data.groups import CONDITION_BY_FACILITY_AND_UNIT as CONDITION, GRADE_BY_FACILITY as GRADE
from .data.conditions import CONDITION_SETTINGS

from kalite.student_testing.utils import get_current_unit_settings_value

from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    student_grade_level = fields.IntegerField(default=0)

# modify ds in-place. Use when you're modifying ds rather than defining new dynamic settings
def modify_dynamic_settings(ds, request=None, user=None):

    user = user or request.session.get('facility_user')

    if user and not user.is_teacher:

        # determine the facility and unit for the current user
        facility = user.facility
        unit = get_current_unit_settings_value(facility.id)

        # look up what condition the user is currently assigned to
        condition = CONDITION.get(facility.id, CONDITION.get(facility.name, CONDITION.get(facility.id[0:8], {}))).get(str(unit), "")

        # Set grade level on students to enable dynamic checking of student playlists within a unit.
        # TODO (richard): (doge) Much hardcode. Such hack. So get rid. Wow.
        ds["ab_testing"].student_grade_level = GRADE.get(facility.id, GRADE.get(facility.name, GRADE.get(facility.id[0:8], 0)))

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
