from annoying.decorators import render_to

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver
from django.http import HttpResponse

from . import AccessLevelExceeded
from .models import CentralLicense
from central.models import Organization
from facility.models import FacilityUser
from securesync.models import DeviceZone, Zone


@receiver(pre_save, sender=DeviceZone)
def restrict_num_devices(sender, instance, **kwargs):
    restrict_data_creation(zone=instance.zone, added_data={"num_devices": 1})

@receiver(pre_save, sender=FacilityUser)
def restrict_num_devices(sender, instance, **kwargs):
    zone = instance.get_zone()
    restrict_data_creation(zone=instance.get_zone(), added_data={"num_facility_users": 1})

@receiver(m2m_changed, sender=Organization.zones.through)
def restrict_num_zones_by_org(sender, action, instance, **kwargs):
    if "pre_add" in action:
        restrict_data_creation(orgs=[instance], added_data={"num_zones": 1})

def restrict_data_creation(orgs=None, zone=None, added_data={}):
    orgs = orgs or (zone and zone.organization_set.all())
    users = [user for org in list(orgs) for user in org.users.all()]
    min_access_level = users and min([CentralLicense.get_access_level(user) for user in users]) or CentralLicense.ACCESS_LEVEL_NONE
    min_access_user = [user for user in users if min_access_level == CentralLicense.get_access_level(user)] or None
    min_access_user = min_access_user and min_access_user[0] or min_access_user

    if not min_access_user:
        return

    #CentralLicense.check_access_limits(user=min_access_user, access_level=min_access_level, added_data=added_data)


def serve_paywall_page(handler):
    def serve_paywall_page_wrapper_fn(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except Exception as ae:
            #if not isinstance(ae, AccessLevelExceeded):
            #    raise
            @render_to('paywall/options.html')
            def dummy(request):
                messages.error(request, ae)

                return {
                    "title": "Value-add features",
                    "error": ae,
                    "current_access_level": CentralLicense.access_level_string(ae.access_level),
                 }
            return dummy(args[1])

    return serve_paywall_page_wrapper_fn


class AccessCheck:
    @serve_paywall_page
    def process_request(self, request):
        if not self.accessing_restricted_page(request):
            logging.debug("Free page: %s" % request.path)
            return

        del request.session['access_level']
        logging.debug("Paid page: %s" % request.path)
        if not "access_level" in request.session:
            request.session['access_level'] = CentralLicense.get_access_level(user=request.user)
        access_level = request.session['access_level']

        CentralLicense.check_access_limits(user=request.user, access_level=request.session['access_level'])

    def accessing_restricted_page(self, request):
        if request.path == reverse("org_management") or "delete" in request.path:  # safety: make sure org overview and delete are always possible.
            return False
        return any([substr in request.path for substr in ["securesync", 'zone', 'organization']])