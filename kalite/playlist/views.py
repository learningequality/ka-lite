from annoying.decorators import render_to


@render_to("playlist/index.html")
def playlists(request):
    context = {
        "title": "Playlists",
    }
    return context
