from .models import Facility, FacilityGroup, FacilityUser


def get_accessible_objects_from_logged_in_user(request, facility):
    """Given a request, get all the facility/group/user objects relevant to the request,
    subject to the permissions of the user type.

    Make sure the returned `facilities` object is always a Facility queryset or an empty list.
    """

    # Options to select.  Note that this depends on the user.
    facilities = []
    if request.user.is_superuser:
        facilities = Facility.objects.all()
        # Groups is now a list of objects with a key for facility id, and a key
        # for the list of groups at that facility.
        # TODO: Make this more efficient.
        groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]

    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        if user.is_teacher:
            facilities = Facility.objects.all()
            groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]
        else:
            # Students can only access their group
            if facility and isinstance(facility, Facility):
                facilities = Facility.objects.filter(id=facility.id)
            if not user.group:
                groups = []
            else:
                groups = [{"facility": user.facility.id,
                           "groups": FacilityGroup.objects.filter(id=request.session["facility_user"].group)}]
    elif facility:
        facilities = Facility.objects.filter(id=facility.id)
        groups = [{"facility": facility.id, "groups": FacilityGroup.objects.filter(facility=facility)}]
    else:
        # defaults to all facilities and groups
        facilities = Facility.objects.all()
        groups = [{"facility": f.id, "groups": FacilityGroup.objects.filter(facility=f)} for f in facilities]

    ungrouped_available = False
    for f in facilities:
        # Check if there is at least one facility with ungrouped students.
        ungrouped_available = f.has_ungrouped_students
        if ungrouped_available:
            break

    return (groups, facilities, ungrouped_available)


def get_users_from_group(user_type, group_id, facility=None):
    if user_type == "coaches":
        user_list = FacilityUser.objects \
            .filter(is_teacher=True) \
            .filter(facility=facility)
    elif group_id == "Ungrouped":
        user_list = FacilityUser.objects \
            .filter(is_teacher=False) \
            .filter(facility=facility, group__isnull=True)
    elif group_id:
        user_list = FacilityUser.objects \
            .filter(facility=facility, group=group_id, is_teacher=False)
    else:
        user_list = FacilityUser.objects \
            .filter(facility=facility, is_teacher=False)

    user_list = user_list \
        .order_by("last_name", "first_name", "username") \
        .prefetch_related("group")

    return user_list

