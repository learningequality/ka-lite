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
    teacher_can_edit_students = fields.BooleanField(default=True)


# these restricted teacher permissions might change on the fly, so
# make sure we update their values based on
# settings.RESTRICTED_TEACHER_PERMISSIONS
def modify_dynamic_settings(ds, request=None, user=None):
    ds["facility"].teacher_can_create_facilities = not settings.RESTRICTED_TEACHER_PERMISSIONS
    ds["facility"].teacher_can_create_students   = not settings.RESTRICTED_TEACHER_PERMISSIONS
    ds["facility"].teacher_can_delete_facilities = not settings.RESTRICTED_TEACHER_PERMISSIONS
    ds["facility"].teacher_can_delete_students   = not settings.RESTRICTED_TEACHER_PERMISSIONS
    ds["facility"].teacher_can_edit_facilities   = not settings.RESTRICTED_TEACHER_PERMISSIONS
    ds["facility"].teacher_can_edit_students     = True
