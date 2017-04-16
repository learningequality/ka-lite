from annoying.decorators import render_to

from kalite.shared.decorators.auth import require_admin


@require_admin
@render_to("playlist/assign_playlists.html")
def assign_playlists(request):
    context = {
        "title": "Playlists",
    }
    return context


@render_to("playlist/view_playlist.html")
def view_playlist(request, playlist_id, channel='playlist'):
    context = {
        'playlist_id': playlist_id,
        'channel': channel,
    }
    return context
