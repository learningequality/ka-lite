from kalite.dynamic_assets import DynamicSettingsBase, fields


class DynamicSettings(DynamicSettingsBase):
    show_store_link_once_points_earned = fields.BooleanField(default=False)
