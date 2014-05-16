import json
import os

from fle_utils.internet import JsonResponse, api_handle_error_with_json

from .models import PlaylistsAssignedToGroup
from kalite.facility.models import FacilityGroup


def sample_json(request):
    jsonfile = os.path.join(os.path.dirname(__file__), 'test_playlist.json')
    with open(jsonfile) as f:
        return JsonResponse(json.load(f))


@api_handle_error_with_json
def assign_group_to_playlist(request, playlist_id, group_id):
    playlist_to_group, was_created = PlaylistsAssignedToGroup.objects.get_or_create(
        playlist=playlist_id,
        group=FacilityGroup.objects.get(id=group_id),
    )

    if was_created:
        return JsonResponse({"ok": "Assigned group %s to playlist %s" % (group_id, playlist_id)})
    else:
        return JsonResponse({"ok": "Playlist already assigned to group"})
