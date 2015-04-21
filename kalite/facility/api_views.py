"""
"""

from annoying.functions import get_object_or_None

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.utils.translation import ugettext as _

from .models import Facility, FacilityGroup, FacilityUser
from fle_utils.internet.decorators import api_response_causes_reload
from fle_utils.internet.classes import JsonResponseMessageSuccess, JsonResponseMessageError
from kalite.shared.decorators.auth import require_authorized_admin


log = settings.LOG


@require_authorized_admin
@api_response_causes_reload
def move_to_group(request):
    users = simplejson.loads(request.body or "{}").get("users", [])
    group_id = simplejson.loads(request.body or "{}").get("group", "")
    group_update = get_object_or_None(FacilityGroup, id=group_id)
    users_to_move = FacilityUser.objects.filter(id__in=users)
    for user in users_to_move:  # can't do update for syncedmodel
        user.group = group_update
        user.save()
    if group_update:
        group_name = group_update.name
    else:
        group_name = group_id
    return JsonResponseMessageSuccess(_("Moved %(num_users)d users to group %(group_name)s successfully.") % {
        "num_users": users_to_move.count(),
        "group_name": group_name,
    })


@require_authorized_admin
@api_response_causes_reload
def delete_users(request):
    users = simplejson.loads(request.body or "{}").get("users", [])
    users_to_delete = FacilityUser.objects.filter(id__in=users)
    count = users_to_delete.count()
    users_to_delete.soft_delete()
    return JsonResponseMessageSuccess(_("Deleted %(num_users)d users successfully.") % {"num_users": count})


@require_authorized_admin
@api_response_causes_reload
def facility_delete(request, facility_id=None):
    if not request.is_django_user:
        raise PermissionDenied("Teachers cannot delete facilities.")

    if request.method != 'POST':
        return JsonResponseMessageError(_("Method is not allowed."), status=405)

    facility_id = facility_id or simplejson.loads(request.body or "{}").get("facility_id")
    fac = get_object_or_404(Facility, id=facility_id)

    fac.soft_delete()
    return JsonResponseMessageSuccess(_("Deleted facility %(facility_name)s successfully.") % {"facility_name": fac.name})


@require_authorized_admin
@api_response_causes_reload
def group_delete(request, group_id=None):
    groups = [group_id] if group_id else simplejson.loads(request.body or "{}").get("groups", [])
    groups_to_delete = FacilityGroup.objects.filter(id__in=groups)
    count = groups_to_delete.count()
    groups_to_delete.soft_delete()
    return JsonResponseMessageSuccess(_("Deleted %(num_groups)d group(s) successfully.") % {"num_groups": count})
