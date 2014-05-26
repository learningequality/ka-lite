from annoying.decorators import render_to

from kalite.shared.decorators import require_login


@require_login
@render_to("playlist/assign_playlists.html")
def assign_playlists(request):
    context = {
        "title": "Playlists",
    }
    return context


@render_to("playlist/view_playlist.html")
def view_playlist(request):
    return {}
