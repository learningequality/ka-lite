from annoying.decorators import render_to

from django.http import HttpResponseForbidden

from kalite.shared.decorators import require_login


@require_login
@render_to("playlist/assign_playlists.html")
def playlists(request):
    if request.is_admin or not request.session['facility_user'].is_teacher:
        return HttpResponseForbidden('Only teachers are allowed to access this page')

    context = {
        "title": "Playlists",
    }
    return context
