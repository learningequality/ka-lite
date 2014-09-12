from django.conf import settings

from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    turn_on_points_for_practice_exams = fields.BooleanField(default=False)


