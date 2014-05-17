from annoying.decorators import render_to

from django.http import HttpResponseForbidden

from kalite.shared.decorators import require_login


@require_login
@render_to("playlist/assign_playlists.html")
def playlists(request):
    context = {
        "title": "Playlists",
    }
    return context
