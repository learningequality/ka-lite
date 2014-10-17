from annoying.decorators import render_to

from kalite.shared.decorators import require_login


@require_login
@render_to("playlist/assign_playlists.html")
def assign_playlists(request):
    # admin doesn't have a facility
    try:
        facility_id = request.session['facility_user'].facility.id
    except:
        facility_id = ""
    context = {
        "title": "Playlists",
        "facility_id" : facility_id,
    }
    return context


@render_to("playlist/view_playlist.html")
def view_playlist(request, playlist_id):
    context = {
        'playlist_id': playlist_id
    }
    return context
