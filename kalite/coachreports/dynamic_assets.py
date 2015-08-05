from django.conf import settings

from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    default_coach_report_day_range = fields.IntegerField(default=getattr(settings, "DEFAULT_COACH_REPORT_DAY_RANGE", 7), minimum=0)