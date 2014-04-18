from django.utils.translation import ugettext as _

from .models import FacilityUser


def get_users_from_group(user_type, group_id, facility=None):
    if user_type == "coaches":
        user_list = FacilityUser.objects \
            .filter(is_teacher=True) \
            .filter(facility=facility)
    elif _(group_id) == _("Ungrouped"):
        user_list = FacilityUser.objects \
            .filter(is_teacher=False) \
            .filter(facility=facility, group__isnull=True)
    elif group_id:
        user_list = FacilityUser.objects \
            .filter(facility=facility, group=group_id, is_teacher=False)
    else:
        user_list = FacilityUser.objects \
            .filter(facility=facility, is_teacher=False)

    user_list = user_list \
        .order_by("last_name", "first_name", "username") \
        .prefetch_related("group")

    return user_list

