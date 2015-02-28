"""
"""
from annoying.functions import get_object_or_None

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from kalite.facility.decorators import facility_from_request
from kalite.facility.models import FacilityUser
from securesync.models import Device, Zone


def get_user_from_request(handler=None, request=None, *args, **kwargs):
    """
    Gets ID of requested user (not necessarily the user logged in)
    """
    assert handler or request
    if not handler:
        handler = lambda request, user, *args, **kwargs: user

    def get_user_from_request_wrapper_fn(request, *args, **kwargs):
        user = get_object_or_None(FacilityUser, id=request.REQUEST["user"]) if "user" in request.REQUEST else None  # don't hit DB if we don't have to
        user = user or request.session.get("facility_user", None)
        return handler(request, *args, user=user, **kwargs)
    return get_user_from_request_wrapper_fn if not request else get_user_from_request_wrapper_fn(request=request, *args, **kwargs)

def require_login(handler):
    """
   (Level 1) Make sure that a user is logged in to the distributed server.
    """
    def require_login_wrapper_fn(request, *args, **kwargs):
        if getattr(request, "is_logged_in", False):  # requires the securesync.middleware.AuthFlags middleware be hit
            return handler(request, *args, **kwargs)

        # Failed.  Send different response for ajax vs non-ajax requests.
        raise PermissionDenied(_("You must be logged in to access this page."))
    return require_login_wrapper_fn


def require_admin(handler):
    """
    Level 2: Require an admin:
    * Central server: any user with an account
    * Distributed server: any Django admin or teacher.

    Note: different behavior for api_request or not
    Note2: we allow users to 'access themselves'
    """

    @require_login
    def require_admin_wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)

        # Allow users to edit themselves 
        facility_user_id = kwargs.get("facility_user_id", None)
        if facility_user_id == request.session.get('facility_user').id:
            return handler(request, *args, **kwargs)

        # Only here if user is not authenticated.
        # Don't redirect users to login for an API request.
        raise PermissionDenied(_("You must be logged in as an admin to access this page."))

    return require_admin_wrapper_fn




def require_authorized_access_to_student_data(handler):
    """
    WARNING: this is a crappy function with a crappy name.

    This should only be used for limiting data access to single-student data.

    Students requesting their own data (either implicitly, without querystring params)
    or explicitly (specifying their own user ID) get through.
    Admins and teachers also get through.
    """
    if settings.CENTRAL_SERVER:
        return require_authorized_admin(handler)

    else:
        @require_login
        def require_authorized_access_to_student_data_wrapper_fn_distributed(request, *args, **kwargs):
            """
            Everything is allowed for admins on distributed server.
            For students, they can only access their own account.
            """
            if getattr(request, "is_admin", False):
                return handler(request, *args, **kwargs)
            else:
                user = get_user_from_request(request=request)
                if request.session.get("facility_user", None) == user:
                    return handler(request, *args, **kwargs)
                else:
                    raise PermissionDenied(_("You requested information for a user that you are not authorized to view."))
            return require_admin(handler)
        return require_authorized_access_to_student_data_wrapper_fn_distributed


def require_authorized_admin(handler):
    """
    Level 1.5 or 2.5 :) : require an admin user that has access to all requested objects.

    Central server: this is by organization permissions.
    Distributed server: you have to be an admin (Django admin/teacher), or requesting only your own user data.

    For testing purposes:
    * distributed server: superuser, teacher, student
    * central server: device not on zone/org, facility not on zone/org, zone not in org, zone with one org, zone with multi orgs, etc
    """

    @require_admin
    def require_authorized_admin_wrapper_fn_central(request, *args, **kwargs):
        """
        The check for distributed servers already exists (require_login), so just use that below.
        All this nuance is for the central server only.
        """
        # inline import, to avoid unnecessary dependency on central server module
        #    on the distributed server.
        from centralserver.central.models import Organization

        logged_in_user = request.user
        assert not logged_in_user.is_anonymous(), "Wrapped by login_required!"

        # Take care of superusers (Django admins).
        if logged_in_user.is_superuser:
            return handler(request, *args, **kwargs)


        # Objects we're looking to verify
        org = None; org_id      = kwargs.get("org_id", None)
        zone = None; zone_id     = kwargs.get("zone_id", None)
        facility = facility_from_request(request=request, *args, **kwargs)
        device = None; device_id   = kwargs.get("device_id", None)
        user = get_user_from_request(request=request, *args, **kwargs)

        # Validate user through facility
        if user:
            if not facility:
                facility = user.facility

        # Validate device through zone
        if device_id:
            device = get_object_or_404(Device, pk=device_id)
            if not zone_id:
                zone = device.get_zone()
                if not zone:
                    raise PermissionDenied(_("You requested device information for a device without a sharing network.  Only super users can do this!"))
                zone_id = zone.pk

        # Validate device through zone
        if facility:
            if not zone_id:
                zone = facility.get_zone()
                if not zone:
                    raise PermissionDenied(_("You requested facility information for a facility with no sharing network.  Only super users can do this!"))
                zone_id = zone.pk

        # Validate zone through org
        if zone_id and zone_id != "new":
            zone = get_object_or_404(Zone, pk=zone_id)
            if not org_id:
                # Have to check if any orgs are accessible to this user.
                for org in Organization.from_zone(zone):
                    if org.is_member(logged_in_user):
                        return handler(request, *args, **kwargs)
                raise PermissionDenied(_("You requested information from an organization that you're not authorized on."))

        if org_id and org_id != "new":
            org = get_object_or_404(Organization, pk=org_id)
            if not org.is_member(logged_in_user):
                raise PermissionDenied(_("You requested information from an organization that you're not authorized on."))
            elif zone_id and zone and org.zones.filter(pk=zone.pk).count() == 0:
                raise PermissionDenied(_("This organization is not linked to the requested sharing network."))

        # Made it through, we're safe!
        return handler(request, *args, **kwargs)

    # This is where the actual distributed server check is done (require_admin)
    return require_authorized_admin_wrapper_fn_central if settings.CENTRAL_SERVER else require_admin(handler)


def require_superuser(handler):
    """
    Level 4: require a Django admin (superuser)

    ***
    *** Note: Not yet used, nor tested. ***
    ***

    """
    def require_superuser_wrapper_fn(request, *args, **kwargs):
        if getattr(request.user, is_superuser, False):
            return handler(request, *args, **kwargs)
        else:
            raise PermissionDenied(_("You must be logged in as a superuser to access this endpoint."))
    return require_superuser_wrapper_fn
