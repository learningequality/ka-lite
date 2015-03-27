"""
"""
import sys

from django.conf import settings
from django.utils import unittest

from ..models import *
from securesync.models import *


class SecuresyncUnicodeModelsTest(unittest.TestCase):
    """
    """
    
    korean_string = unichr(54392)
    
    def test_unicode_string(self):
        # Stand-alone classes
        dev = Device(name=self.korean_string)
        self.assertNotIn(unicode(dev), "Bad Unicode data", "Device: Bad conversion to unicode.")

        fac = Facility(name=self.korean_string)
        self.assertNotIn(unicode(fac), "Bad Unicode data", "Facility: Bad conversion to unicode.")

        fg = FacilityGroup(facility=fac, name=self.korean_string)
        self.assertNotIn(unicode(fg), "Bad Unicode data", "FacilityGroup: Bad conversion to unicode.")

        zon = Zone(name=self.korean_string)
        self.assertNotIn(unicode(zon), "Bad Unicode data", "Zone: Bad conversion to unicode.")

        # Classes using other classes
        fu = FacilityUser(
            facility=fac,
            group=fg,
            first_name=self.korean_string,
            last_name=self.korean_string,
            username=self.korean_string,
            notes=self.korean_string,
        )
        fu.set_password(self.korean_string * settings.PASSWORD_CONSTRAINTS["min_length"]),
        self.assertNotIn(unicode(fu), "Bad Unicode data", "FacilityUser: Bad conversion to unicode.")

        syncsess = SyncSession(
            client_device=dev,
            server_device=dev,
            client_nonce=self.korean_string,
            server_nonce=self.korean_string,
            client_version=self.korean_string,
            client_os=self.korean_string,
        )
        self.assertNotIn(unicode(syncsess), "Bad Unicode data", "SyncSession: Bad conversion to unicode.")

        dz = DeviceZone(device=dev, zone=zon)
        self.assertNotIn(unicode(dz), "Bad Unicode data", "DeviceZone: Bad conversion to unicode.")

        pkey = RegisteredDevicePublicKey(zone=zon, public_key=self.korean_string)
        self.assertNotIn(unicode(pkey), "Bad Unicode data", "RegisteredDevicePublicKey: Bad conversion to unicode.")
