"""
"""
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.utils.translation import ugettext as _

from .models import Facility, FacilityGroup, FacilityUser
from fle_utils.internet import api_handle_error_with_json, JsonResponseMessageSuccess, JsonResponseMessageError
from kalite.shared.decorators import require_admin


@require_admin
@api_handle_error_with_json
def move_to_group(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    group = simplejson.loads(request.raw_post_data or "{}").get("group", "")
    if group == _("Ungrouped"):
        group_update = None
    else:
        group_update = FacilityGroup.objects.get(pk=group)
    users_to_move = FacilityUser.objects.filter(username__in=users)
    users_to_move.update(group=group_update)
    if group_update:
        group_name = group_update.name
    else:
        group_name = group
    return JsonResponseMessageSuccess(_("Moved %(num_users)d users to group %(group_name)s successfully.") % {
        "num_users": users_to_move.count(),
        "group_name": group_name,
    })


@require_admin
@api_handle_error_with_json
def delete_users(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    users_to_delete = FacilityUser.objects.filter(username__in=users)
    users_to_delete.delete()
    return JsonResponseMessageSuccess(_("Deleted %(num_users)d users successfully.") % {"num_users": users_to_delete.count()})


@require_admin
@api_handle_error_with_json
def facility_delete(request, facility_id=None):
    if not request.is_django_user:
        raise PermissionDenied("Teachers cannot delete facilities.")

    facility_id = facility_id or simplejson.loads(request.raw_post_data or "{}").get("facility_id")
    fac = get_object_or_404(Facility, id=facility_id)
    if not fac.is_deletable():
        return JsonResponseMessageError(_("Facility %(facility_name)s is not deletable.") % {"facility_name": fac.name})

    fac.delete()
    return JsonResponseMessageSuccess(_("Deleted facility %(facility_name)s successfully.") % {"facility_name": fac.name})

