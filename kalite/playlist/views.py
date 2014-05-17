from annoying.decorators import render_to


@render_to("playlist/assign_playlists.html")
def playlists(request):
    context = {
        "title": "Playlists",
    }
    return context
