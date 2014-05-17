from fle_utils.internet import JsonResponse, api_handle_error_with_json

from .models import PlaylistToGroupMapping
from kalite.facility.models import FacilityGroup


@api_handle_error_with_json
def assign_group_to_playlist(request, playlist_id, group_id):
    playlist_to_group, was_created = PlaylistToGroupMapping.objects.get_or_create(
        playlist=playlist_id,
        group=FacilityGroup.objects.get(id=group_id),
    )

    if was_created:
        return JsonResponse({"ok": "Assigned group %s to playlist %s" % (group_id, playlist_id)})
    else:
        return JsonResponse({"ok": "Playlist already assigned to group"})
