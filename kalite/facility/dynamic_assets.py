from django.conf import settings
from kalite.dynamic_assets import DynamicSettingsBase, fields


class DynamicSettings(DynamicSettingsBase):
    show_store_link_once_points_earned = fields.BooleanField(default=False)

    # Teacher restrictions
    teacher_can_create_facilities = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
    teacher_can_create_students = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
    teacher_can_delete_facilities = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
    teacher_can_delete_students = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
    teacher_can_edit_facilities = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
    teacher_can_edit_students = fields.BooleanField(default=not settings.RESTRICTED_TEACHER_PERMISSIONS)
