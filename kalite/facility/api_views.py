from django.utils import simplejson


from .models import FacilityGroup, FacilityUser
from shared.decorators import require_admin
from utils.internet import api_handle_error_with_json, JsonResponse

# Views below are for user management endpoints


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
