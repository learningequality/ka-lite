from annoying.decorators import render_to

from kalite.facility.models import Facility, FacilityUser


n_users_created = 0  # keep a global, to let us know if we've initialized, or need to re-initialize.

@render_to("loadtesting/load_test.html")
def load_test(request, nusers=None):
    global n_users_created

    if not n_users_created or n_users_created < int(request.GET.get("nusers", 1)):  # default 1, as before
        # It's either the first time, or time to add more

        # Make sure there's a facility
        if not Facility.objects.count():
            fac = Facility.objects.create(name="fac")
        fac = Facility.objects.all()[0]

        # Loop over all needed students
        while n_users_created < int(request.GET.get("nusers", 1)):
            n_users_created += 1
            unpw = "s%d" % n_users_created
            (user, _) = FacilityUser.get_or_initialize(username=unpw, facility=fac)
            user.set_password(unpw)
            user.save()

    return {
        "pct_videos": request.GET.get("pct_videos", 0.9),
        "pct_logout": request.GET.get("pct_logout", 0.0),
        "nusers": n_users_created,
    }