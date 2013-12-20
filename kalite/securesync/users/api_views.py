from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson

from securesync.models import FacilityGroup, FacilityUser
from shared.decorators import allow_api_profiling, require_admin
from utils.internet import api_handle_error_with_json, JsonResponse

# Functions below here focused on users

@require_admin
@api_handle_error_with_json
def remove_from_group(request):
    """
    API endpoint for removing users from group
    (from user management page)
    """
    users = simplejson.loads(request.raw_post_data or "{}").get("users", "")
    users_to_remove = FacilityUser.objects.filter(username__in=users)
    users_to_remove.update(group=None)
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def move_to_group(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    group = simplejson.loads(request.raw_post_data or "{}").get("group", "")
    group_update = FacilityGroup.objects.get(pk=group)
    users_to_move = FacilityUser.objects.filter(username__in=users)
    users_to_move.update(group=group_update)
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def delete_users(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    users_to_delete = FacilityUser.objects.filter(username__in=users)
    users_to_delete.delete()
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def facility_delete(request, facility_id=None):
    if not request.is_django_user:
        raise PermissionDenied("Teachers cannot delete facilities.")

    facility_id = facility_id or simplejson.loads(request.raw_post_data or "{}").get("facility_id")
    fac = get_object_or_404(Facility, id=facility_id)
    if not fac.is_deletable():
        return HttpResponseForbidden("")

    fac.delete()
    return JsonResponse({})

