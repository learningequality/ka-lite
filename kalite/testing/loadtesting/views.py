import uuid

from annoying.decorators import render_to

from kalite.facility.models import Facility, FacilityUser

@render_to("distributed/loadtesting/load_test.html")
def load_test(request, nusers=None):
    """
    The principal purpose of this view is to allow the automated testing of multiple clients
    connected to the server at once, interacting in a way that is at least somewhat representative
    of normal user behaviour.

    As such, navigating to the loadtesting page on a client device will load an iframe which will
    then use Javascript to automate user interaction with the site. It will try to watch videos and
    do exercises in rapid succession in order to put strain on the server and associated network
    connections.

    So far the principal use for this has been testing with 30+ tablets connected over WiFi to a
    server and seeing if the server and wireless connection can handle the strain.
    """

    username = uuid.uuid4().hex[:12]

    # Make sure there's a facility
    if not Facility.objects.count():
        fac = Facility.objects.create(name="fac")
    fac = Facility.objects.all()[0]

    # Create the user
    (user, _) = FacilityUser.get_or_initialize(username=username, facility=fac)
    user.set_password(username)
    user.save()

    return {
        "pct_videos": request.GET.get("pct_videos", 0.3),
        "username": username,
    }