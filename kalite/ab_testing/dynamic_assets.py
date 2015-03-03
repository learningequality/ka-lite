from .data.groups import get_grade_by_facility
from .data.conditions import CONDITION_SETTINGS

from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    student_grade_level = fields.IntegerField(default=0)

# modify ds in-place. Use when you're modifying ds rather than defining new dynamic settings
def modify_dynamic_settings(ds, request=None, user=None):

    user = user or request.session.get('facility_user')

    if user and not user.is_teacher:

        # determine the facility for the current user
        facility = user.facility

        # TODO (richard): (doge) Much hardcode. Such hack. So get rid. Wow.
        ds["ab_testing"].student_grade_level = get_grade_by_facility(facility)
