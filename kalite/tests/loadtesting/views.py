from annoying.decorators import render_to

from securesync.models import Facility, FacilityUser


users_are_created = False
@render_to("loadtesting/load_test.html")
def load_test(request):
    global users_are_created

    if not users_are_created:
        if not Facility.objects.count() > 0:
            fac = Facility.create({ "name": "fac" })
        fac = Facility.objects.all()[0]
        for sidx in range(1, 11):
            unpw = "s%d" % sidx
            user = FacilityUser.get_or_initialize(username=unpw, facility=fac)
            user.set_password(unpw)
            user.save()
        users_are_created = True

    return {}