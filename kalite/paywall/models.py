import datetime

import django_snippets.multiselect as multiselect
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from . import AccessLevelExceeded
from central.models import Organization
from facility.models import FacilityUser
from securesync.models import Device
from utils.django_utils import ExtendedModel
from utils.general import datediff


class CentralLicense(ExtendedModel):
    """License defines an org, and potentially a single user, what they have access to, and for what period."""

    ACCESS_LEVEL_NONE = 0
    ACCESS_LEVEL_BASIC = 1
    ACCESS_LEVEL_PLUS = 2
    ACCESS_LEVEL_PREMIUM = 3
    ACCESS_LEVEL_ELITE = 4
    ACCESS_LEVELS = ((ACCESS_LEVEL_BASIC, 'Basic'),
                     (ACCESS_LEVEL_PLUS, 'Plus'),
                     (ACCESS_LEVEL_PREMIUM, 'Premium'),
                     (ACCESS_LEVEL_ELITE, 'Elite'))

    ACCESS_LIMITS = {  # tuple of max #: zones, registered devices, facility users
        ACCESS_LEVEL_BASIC:   (1, 1, 20),
        ACCESS_LEVEL_PLUS:    (2, 5, 50),
        ACCESS_LEVEL_PREMIUM: (5, 25, 500),
        ACCESS_LEVEL_ELITE: (None, None, None),
    }
    org       = models.ForeignKey(Organization)
    user      = models.ForeignKey(User, blank=True, null=True)
    access_level = models.IntegerField(choices=ACCESS_LEVELS, null=True)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def has_access(self, access_level):
        return (self.start_datetime is None or datediff(self.start_date, datetime.datetime.now()) <= 0) \
            and (self.end_datetime is None or datediff(self.end_date, datetime.datetime.now()) >= 0) \
            and (self.access_level is not None and self.access_level >= access_level)

    @classmethod
    def access_level_string(cls, access_level):
        str = [al[1] for al in CentralLicense.ACCESS_LEVELS if al[0] == access_level]
        return str and str[0] or 'None'

    @classmethod
    def get_access_level(cls, user):

        if not user.is_authenticated():
            return cls.ACCESS_LEVEL_NONE
        elif user.is_superuser:
            return cls.ACCESS_LEVEL_BASIC

        levels = cls.objects.filter(models.Q(user=user) | models.Q(user__isnull=True, user__organization__in=list(user.organization_set.all()))) \
            .filter(models.Q(start_datetime__isnull=True) | models.Q(start_datetime__lt=datetime.datetime.now())) \
            .filter(models.Q(end_datetime__isnull=True) | models.Q(end_datetime__gt=datetime.datetime.now()))
        return (levels and max(list(levels))) or cls.ACCESS_LEVEL_NONE

    @classmethod
    def check_access_limits(cls, user, access_level=None, raises=True, added_data={}):
        access_level = access_level is None and cls.get_access_level(user) or access_level

        org_set = user.is_authenticated() and list(user.organization_set.all()) or []
        zone_set = [z for org in org_set for z in org.zones.all()]
        fu_count = sum([FacilityUser.objects.filter(Q(signed_by__devicezone__zone=z) | Q(zone_fallback=z)).count() for z in zone_set])
        dev_count = sum([Device.objects.filter(devicezone__zone=z).count() for z in zone_set])

        al_str = cls.access_level_string(access_level)
        (max_zones, max_devices, max_facilityusers) = CentralLicense.ACCESS_LIMITS[access_level]

        try:
            if len(zone_set) + added_data.get("num_zones", 0) > max_zones:
                raise AccessLevelExceeded("%s level allows only one sharing network." % al_str, access_level=access_level)
            elif dev_count + added_data.get("num_devices", 0) > max_devices:
                raise AccessLevelExceeded("%s level allows only one device registration." % al_str, access_level=access_level)
            elif fu_count + added_data.get("num_facility_users", 0) > max_facilityusers:
                raise AccessLevelExceeded("%s level allows only 20 facility users." % al_str, access_level=access_level)
            return True
        except AccessLevelExceeded:
            if raises:
                raise
            return False
